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
from google_cloud_pipeline_components.v1.bigquery import BigqueryQueryJobOp
from kfp.v2 import dsl, compiler

from pipelines.config import PredictionConfig
from pipelines.utils import generate_query
from vertex_components import lookup_model, model_batch_predict

config = PredictionConfig()


@dsl.pipeline(name=config.pipeline_name)
def pipeline(
    project_id: str = config.project_id,
    project_location: str = config.project_location,
    ingestion_project_id: str = config.project_id_ingestion,
    model_name: str = config.model_name,
    preprocessing_dataset_id: str = config.preprocessing_dataset_id,
    dataset_location: str = config.dataset_location,
    ingestion_dataset_id: str = config.project_id_ingestion,
    prediction_dataset_id: str = config.prediction_dataset_id,
    timestamp: str = config.timestamp,
    batch_prediction_machine_type: str = config.machine_type,
    batch_prediction_min_replicas: int = config.min_replicas,
    batch_prediction_max_replicas: int = config.max_replicas,
):
    """
    XGB prediction pipeline which:
     1. Looks up the default model version (champion) and
        dataset which was used to the train model.
     2. Runs a BatchPredictionJob with optional training-serving skew detection.

    Args:
        project_id (str): project id of the Google Cloud project
        project_location (str): location of the Google Cloud project
        ingestion_project_id (str): project id containing the source bigquery data
            for ingestion. This can be the same as `project_id` if the source data is
            in the same project where the ML pipeline is executed.
        model_name (str): name of model
        preprocessing_dataset_id (str): id of BQ dataset used to
            store all staging data .
        prediction_dataset_id (str): id of BQ dataset used to
            store all predictions.
        dataset_location (str): location of dataset
        ingestion_dataset_id (str): dataset id of ingestion data
        timestamp (str): Optional. Empty or a specific timestamp in ISO 8601 format
            (YYYY-MM-DDThh:mm:ss.sss±hh:mm or YYYY-MM-DDThh:mm:ss).
            If any time part is missing, it will be regarded as zero.
        batch_prediction_machine_type (str): Machine type to be used for Vertex Batch
            Prediction. Example machine_types - n1-standard-4, n1-standard-16 etc.
        batch_prediction_min_replicas (int): Minimum no of machines to distribute the
            Vertex Batch Prediction job for horizontal scalability
        batch_prediction_max_replicas (int): Maximum no of machines to distribute the
            Vertex Batch Prediction job for horizontal scalability.

    Returns:
        None

    """

    # Create variables to ensure the same arguments are passed
    # into different components of the pipeline

    # data ingestion and preprocessing operations
    preprocessing_query = generate_query(
        config.query_file,
        source_dataset=f"{ingestion_project_id}.{ingestion_dataset_id}",
        source_table=config.ingestion_table,
        prediction_dataset=f"{ingestion_project_id}.{prediction_dataset_id}",
        preprocessing_dataset=f"{ingestion_project_id}.{preprocessing_dataset_id}",
        ingested_table=config.ingested_table,
        dataset_region=project_location,
        filter_column=config.time_col,
        filter_start_value=timestamp,
    )

    preprocessing = BigqueryQueryJobOp(
        project=project_id, location=dataset_location, query=preprocessing_query
    ).set_display_name("Ingest data")

    # lookup champion model
    champion_model = (
        lookup_model(
            model_name=model_name,
            project_location=project_location,
            project_id=project_id,
            fail_on_model_not_found=True,
        )
        .set_display_name("Look up champion model")
        .set_caching_options(False)
    )

    # batch predict from BigQuery to BigQuery
    bigquery_source_input_uri = (
        f"bq://{project_id}.{preprocessing_dataset_id}.{config.ingested_table}"
    )
    bigquery_destination_output_uri = f"bq://{project_id}.{prediction_dataset_id}"

    batch_prediction = (
        model_batch_predict(
            model=champion_model.outputs["model"],
            job_display_name=config.predict_job_name,
            project_location=project_location,
            project_id=project_id,
            source_uri=bigquery_source_input_uri,
            destination_uri=bigquery_destination_output_uri,
            source_format="bigquery",
            destination_format="bigquery",
            machine_type=batch_prediction_machine_type,
            starting_replica_count=batch_prediction_min_replicas,
            max_replica_count=batch_prediction_max_replicas,
            monitoring_training_dataset=champion_model.outputs["training_dataset"],
            monitoring_alert_email_addresses=config.monitoring_alert_email_addresses,
            monitoring_skew_config=config.monitoring_skew_config,
            instance_config=config.instance_config,
        )
        .after(preprocessing)
        .set_display_name("Batch prediction job")
    )


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path="predict.json",
        type_check=False,
    )
