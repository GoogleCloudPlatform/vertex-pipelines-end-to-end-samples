# Copyright 2022 Google LLC
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

import os
import pathlib

from google_cloud_pipeline_components.v1.bigquery import BigqueryQueryJobOp
from kfp import dsl
from kfp.dsl import Dataset, Input, Metrics, Model, Output, OutputPath
from pipelines import generate_query
from bigquery_components import extract_bq_to_dataset
from vertex_components import upload_model

CONTAINER_IMAGE_REGISTRY = os.environ["CONTAINER_IMAGE_REGISTRY"]
RESOURCE_SUFFIX = os.environ.get("RESOURCE_SUFFIX", "default")
TRAINING_IMAGE = f"{CONTAINER_IMAGE_REGISTRY}/training:{RESOURCE_SUFFIX}"
SERVING_IMAGE = f"{CONTAINER_IMAGE_REGISTRY}/serving:{RESOURCE_SUFFIX}"


@dsl.container_component
def train(
    train_data: Input[Dataset],
    valid_data: Input[Dataset],
    test_data: Input[Dataset],
    model: Output[Model],
    model_output_uri: OutputPath(str),
    metrics: Output[Metrics],
    hparams: dict,
):
    return dsl.ContainerSpec(
        image=TRAINING_IMAGE,
        command=["python"],
        args=[
            "training/train.py",
            "--train-data",
            train_data.path,
            "--valid-data",
            valid_data.path,
            "--test-data",
            test_data.path,
            "--model",
            model.path,
            "--model-output-uri",
            model_output_uri,
            "--metrics",
            metrics.path,
            "--hparams",
            hparams,
        ],
    )


@dsl.pipeline(name="xgboost-train-pipeline")
def pipeline(
    project_id: str = os.environ.get("VERTEX_PROJECT_ID"),
    project_location: str = os.environ.get("VERTEX_LOCATION"),
    ingestion_project_id: str = os.environ.get("VERTEX_PROJECT_ID"),
    model_name: str = "simple_xgboost",
    dataset_id: str = "preprocessing",
    dataset_location: str = os.environ.get("VERTEX_LOCATION"),
    ingestion_dataset_id: str = "chicago_taxi_trips",
    timestamp: str = "2022-12-01 00:00:00",
    resource_suffix: str = os.environ.get("RESOURCE_SUFFIX"),
    test_dataset_uri: str = "",
):
    """
    XGB training pipeline which:
     1. Splits and extracts a dataset from BQ to GCS
     2. Trains a model via Vertex AI CustomTrainingJob
     3. Evaluates the model against the current champion model
     4. If better the model becomes the new default model

    Args:
        project_id (str): project id of the Google Cloud project
        project_location (str): location of the Google Cloud project
        ingestion_project_id (str): project id containing the source bigquery data
            for ingestion. This can be the same as `project_id` if the source data is
            in the same project where the ML pipeline is executed.
        model_name (str): name of model
        dataset_id (str): id of BQ dataset used to store all staging data & predictions
        dataset_location (str): location of dataset
        ingestion_dataset_id (str): dataset id of ingestion data
        timestamp (str): Optional. Empty or a specific timestamp in ISO 8601 format
            (YYYY-MM-DDThh:mm:ss.sss±hh:mm or YYYY-MM-DDThh:mm:ss).
            If any time part is missing, it will be regarded as zero.
        resource_suffix (str): Optional. Additional suffix to append GCS resources
            that get overwritten.
        test_dataset_uri (str): Optional. GCS URI of statis held-out test dataset.
    """

    # Create variables to ensure the same arguments are passed
    # into different components of the pipeline
    label_column_name = "total_fare"
    time_column = "trip_start_timestamp"
    ingestion_table = "taxi_trips"
    table_suffix = f"_xgb_training_{resource_suffix}"  # suffix to table names
    ingested_table = "ingested_data" + table_suffix
    preprocessed_table = "preprocessed_data" + table_suffix
    train_table = "train_data" + table_suffix
    valid_table = "valid_data" + table_suffix
    test_table = "test_data" + table_suffix
    primary_metric = "rootMeanSquaredError"
    hparams = dict(
        n_estimators=200,
        early_stopping_rounds=10,
        objective="reg:squarederror",
        booster="gbtree",
        learning_rate=0.3,
        min_split_loss=0,
        max_depth=6,
        label=label_column_name,
    )

    # generate sql queries which are used in ingestion and preprocessing
    # operations

    queries_folder = pathlib.Path(__file__).parent / "queries"

    preprocessing_query = generate_query(
        queries_folder / "preprocessing.sql",
        source_dataset=f"{ingestion_project_id}.{ingestion_dataset_id}",
        source_table=ingestion_table,
        preprocessing_dataset=f"{ingestion_project_id}.{dataset_id}",
        ingested_table=ingested_table,
        dataset_region=project_location,
        filter_column=time_column,
        target_column=label_column_name,
        filter_start_value=timestamp,
        train_table=train_table,
        validation_table=valid_table,
        test_table=test_table,
    )

    preprocessing = BigqueryQueryJobOp(
        project=project_id, location=dataset_location, query=preprocessing_query
    ).set_display_name("Ingest & preprocess data")

    # data extraction to gcs

    train_dataset = (
        extract_bq_to_dataset(
            bq_client_project_id=project_id,
            source_project_id=project_id,
            dataset_id=dataset_id,
            table_name=train_table,
            dataset_location=dataset_location,
        )
        .after(preprocessing)
        .set_display_name("Extract train data")
        .set_caching_options(False)
    ).outputs["dataset"]
    valid_dataset = (
        extract_bq_to_dataset(
            bq_client_project_id=project_id,
            source_project_id=project_id,
            dataset_id=dataset_id,
            table_name=valid_table,
            dataset_location=dataset_location,
        )
        .after(preprocessing)
        .set_display_name("Extract validation data")
        .set_caching_options(False)
    ).outputs["dataset"]
    test_dataset = (
        extract_bq_to_dataset(
            bq_client_project_id=project_id,
            source_project_id=project_id,
            dataset_id=dataset_id,
            table_name=test_table,
            dataset_location=dataset_location,
            destination_gcs_uri=test_dataset_uri,
        )
        .after(preprocessing)
        .set_display_name("Extract test data")
        .set_caching_options(False)
    ).outputs["dataset"]

    train_model = train(
        train_data=train_dataset,
        valid_data=valid_dataset,
        test_data=test_dataset,
        hparams=hparams,
    ).set_display_name("Train model")

    upload_model_op = upload_model(
        project=project_id,
        location=project_location,
        model_evaluation=train_model.outputs["metrics"],
        eval_metric=primary_metric,
        eval_lower_is_better=True,
        model=train_model.outputs["model"],
        serving_container_image=SERVING_IMAGE,
        model_name=model_name,
        pipeline_job_id="{{$.pipeline_job_name}}",
        test_dataset=test_dataset,
    ).set_display_name("Upload model")
