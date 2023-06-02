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
from os import environ as env

from google_cloud_pipeline_components.v1.bigquery import BigqueryQueryJobOp
from kfp.v2 import dsl
from pipelines.configs import load_config
from pipelines.utils import generate_query
from bigquery_components import extract_bq_to_dataset
from vertex_components import (
    lookup_model,
    custom_train_job,
    import_model_evaluation,
    update_best_model,
)

config = load_config()


@dsl.pipeline(name=config.train_pipeline_name)
def pipeline(
    project_id: str = env.get("VERTEX_PROJECT_ID"),
    project_location: str = env.get("VERTEX_LOCATION"),
    ingestion_project_id: str = env.get("VERTEX_PROJECT_ID"),
    model_name: str = config.model_name,
    dataset_id: str = "preprocessing",
    dataset_location: str = env.get("VERTEX_LOCATION"),
    ingestion_dataset_id: str = "chicago_taxi_trips",
    timestamp: str = "2022-12-01 00:00:00",
    staging_bucket: str = env.get("VERTEX_PIPELINE_ROOT"),
    pipeline_files_gcs_path: str = env.get("PIPELINE_FILES_GCS_PATH"),
    test_dataset_uri: str = config.test_dataset_uri,
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
        staging_bucket (str): Staging bucket for pipeline artifacts.
        pipeline_files_gcs_path (str): GCS path where the pipeline files are located.
        test_dataset_uri (str): Optional. GCS URI of statis held-out test dataset.
    """

    # Create variables to ensure the same arguments are passed
    # into different components of the pipeline
    label_column_name = "total_fare"
    time_column = "trip_start_timestamp"
    ingestion_table = "taxi_trips"
    ingested_table = config.table_prefix + "ingested_data"
    train_table = config.table_prefix + "train_data"
    valid_table = config.table_prefix + "valid_data"
    test_table = config.table_prefix + "test_data"
    primary_metric = "rootMeanSquaredError"
    train_script_uri = f"{pipeline_files_gcs_path}/assets/{config.train_script}"

    # generate sql queries which are used in ingestion and preprocessing
    # operations

    preprocessing_query = generate_query(
        config.train_preprocess_sql,
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

    existing_model = (
        lookup_model(
            model_name=model_name,
            project_location=project_location,
            project_id=project_id,
            fail_on_model_not_found=False,
        )
        .set_display_name("Lookup past model")
        .set_caching_options(False)
        .outputs["model_resource_name"]
    )

    train_model = custom_train_job(
        train_script_uri=train_script_uri,
        train_data=train_dataset,
        valid_data=valid_dataset,
        test_data=test_dataset,
        project_id=project_id,
        project_location=project_location,
        model_display_name=model_name,
        train_container_uri=config.train_container,
        serving_container_uri=config.serve_container,
        hparams=config.train_hparams,
        requirements=config.train_requirements,
        staging_bucket=staging_bucket,
        parent_model=existing_model,
    ).set_display_name("Train model")

    evaluation = import_model_evaluation(
        model=train_model.outputs["model"],
        metrics=train_model.outputs["metrics"],
        test_dataset=test_dataset,
        pipeline_job_id="{{$.pipeline_job_name}}",
        project_location=project_location,
    ).set_display_name("Import evaluation")

    with dsl.Condition(existing_model != "", "champion-exists"):
        update_best_model(
            challenger=train_model.outputs["model"],
            challenger_evaluation=evaluation.outputs["model_evaluation"],
            parent_model=existing_model,
            eval_metric=primary_metric,
            eval_lower_is_better=True,
            project_id=project_id,
            project_location=project_location,
        ).set_display_name("Update best model")
