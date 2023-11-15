# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import pathlib
from os import environ as env

from google_cloud_pipeline_components.v1.bigquery import BigqueryQueryJobOp
from kfp import dsl
from kfp.dsl import Dataset, Input, Metrics, Model, Output

from pipelines.utils.query import generate_query
from components import extract_table, upload_model


LABEL = "total_fare"
PRIMARY_METRIC = "rootMeanSquaredError"
HPARAMS = dict(
    n_estimators=200,
    early_stopping_rounds=10,
    objective="reg:squarederror",
    booster="gbtree",
    learning_rate=0.3,
    min_split_loss=0,
    max_depth=6,
    label=LABEL,
)
RESOURCE_SUFFIX = env.get("RESOURCE_SUFFIX", "default")
TRAINING_IMAGE = f"{env['CONTAINER_IMAGE_REGISTRY']}/training:{RESOURCE_SUFFIX}"
SERVING_IMAGE = f"{env['CONTAINER_IMAGE_REGISTRY']}/serving:{RESOURCE_SUFFIX}"


@dsl.container_component
def train(
    input_data: Input[Dataset],
    input_test_path: str,
    hparams: dict,
    train_data: Output[Dataset],
    valid_data: Output[Dataset],
    test_data: Output[Dataset],
    model: Output[Model],
    metrics: Output[Metrics],
):
    return dsl.ContainerSpec(
        image=TRAINING_IMAGE,
        command=["python"],
        args=[
            "-m" "training",
            "--input_path",
            input_data.path,
            dsl.IfPresentPlaceholder(
                input_name="input_test_path",
                then=["--input_test_path", input_test_path],
            ),
            "--hparams",
            hparams,
            "--output_train_path",
            train_data.path,
            "--output_valid_path",
            valid_data.path,
            "--output_test_path",
            test_data.path,
            "--output_model",
            model.path,
            "--output_metrics",
            metrics.path,
        ],
    )


@dsl.pipeline(name="turbo-training-pipeline")
def pipeline(
    project: str = env.get("VERTEX_PROJECT_ID"),
    location: str = env.get("VERTEX_LOCATION"),
    bq_location: str = env.get("BQ_LOCATION"),
    bq_source_uri: str = "bigquery-public-data.chicago_taxi_trips.taxi_trips",
    model_name: str = "xgb_regressor",
    dataset: str = "turbo_templates",
    timestamp: str = "2022-12-01 00:00:00",
    test_data_gcs_uri: str = "",
):
    """
    Training pipeline which:
     1. Preprocesses data in BigQuery
     2. Extracts data to Cloud Storage
     3. Trains a model using a custom prebuilt container
     4. Uploads the model to Model Registry
     5. Evaluates the model against a champion model
     6. Selects a new champion based on the primary metrics

    Args:
        project (str): project id of the Google Cloud project
        location (str): location of the Google Cloud project
        bq_location (str): location of dataset in BigQuery
        bq_source_uri (str): `<project>.<dataset>.<table>` of ingestion data in BigQuery
        model_name (str): name of model
        dataset (str): dataset id to store staging data & predictions in BigQuery
        timestamp (str): Optional. Empty or a specific timestamp in ISO 8601 format
            (YYYY-MM-DDThh:mm:ss.sss±hh:mm or YYYY-MM-DDThh:mm:ss).
            If any time part is missing, it will be regarded as zero.
        test_data_gcs_uri (str): Optional. GCS URI of static held-out test dataset.
    """

    table = f"prep_training_{RESOURCE_SUFFIX}"
    queries_folder = pathlib.Path(__file__).parent / "queries"

    prep_query = generate_query(
        queries_folder / "preprocessing.sql",
        source=bq_source_uri,
        location=bq_location,
        dataset=f"{project}.{dataset}",
        table=table,
        label=LABEL,
        start_timestamp=timestamp,
    )

    prep_op = BigqueryQueryJobOp(
        project=project,
        location=bq_location,
        query=prep_query,
    ).set_display_name("Ingest & preprocess data")

    data_op = (
        extract_table(
            project=project,
            location=bq_location,
            table=f"{project}:{dataset}.{table}",
        )
        .after(prep_op)
        .set_display_name("Extract data")
    )

    train_op = train(
        input_data=data_op.outputs["data"],
        input_test_path=test_data_gcs_uri,
        hparams=HPARAMS,
    ).set_display_name("Train model")

    upload_model(
        project=project,
        location=location,
        model=train_op.outputs["model"],
        model_evaluation=train_op.outputs["metrics"],
        test_data=train_op.outputs["test_data"],
        eval_metric=PRIMARY_METRIC,
        eval_lower_is_better=True,
        serving_container_image=SERVING_IMAGE,
        model_name=model_name,
        model_description="Predict price of a taxi trip.",
        pipeline_job_id="{{$.pipeline_job_name}}",
    ).set_display_name("Upload model")
