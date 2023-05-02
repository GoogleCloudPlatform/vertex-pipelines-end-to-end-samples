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

import json
import os
import pathlib

from kfp.v2 import compiler, dsl

from pipelines import generate_query
from pipelines.components import (
    lookup_model,
    extract_bq_to_dataset,
    bq_query_to_table,
    load_dataset_to_bq,
    model_batch_predict,
    wait_gcp_resources,
)


@dsl.pipeline(name="tensorflow-prediction-pipeline")
def tensorflow_pipeline(
    project_id: str = os.environ.get("VERTEX_PROJECT_ID"),
    project_location: str = os.environ.get("VERTEX_LOCATION"),
    ingestion_project_id: str = os.environ.get("VERTEX_PROJECT_ID"),
    model_name: str = "tensorflow_with_preprocessing",
    model_label: str = "label_name",
    dataset_id: str = "preprocessing",
    dataset_location: str = os.environ.get("VERTEX_LOCATION"),
    ingestion_dataset_id: str = "chicago_taxi_trips",
    timestamp: str = "2022-12-01 00:00:00",
    batch_prediction_machine_type: str = "n1-standard-4",
    batch_prediction_min_replicas: int = 3,
    batch_prediction_max_replicas: int = 10,
):
    """
    Tensorflow prediction pipeline which:
     1. Extracts a dataset from BQ
     2. Validates training/serving skew
     3. Scores data to produce predictions
     4. Post-processes predictions
     5. Loads predictions into BQ

    Args:
        project_id (str): project id of the Google Cloud project
        project_location (str): location of the Google Cloud project
        pipeline_files_gcs_path (str): GCS path where the pipeline files are located
        ingestion_project_id (str): project id containing the source bigquery data
            for ingestion. This can be the same as `project_id` if the source data is
            in the same project where the ML pipeline is executed.
        model_name (str): name of model
        model_label (str): label of model
        dataset_id (str): id of BQ dataset used to store all staging data & predictions
        dataset_location (str): location of dataset
        ingestion_dataset_id (str): dataset id of ingestion data
        timestamp (str): Optional. Empty or a specific timestamp in ISO 8601 format
            (YYYY-MM-DDThh:mm:ss.sss±hh:mm or YYYY-MM-DDThh:mm:ss).
            If any time part is missing, it will be regarded as zero.
        batch_prediction_machine_type (str): Machine type to be used for Vertex Batch
            Prediction. Example machine_types - n1-standard-4, n1-standard-16 etc
        batch_prediction_min_replicas (int): Minimum no of machines to distribute the
            Vertex Batch Prediction job for horizontal scalability
        batch_prediction_max_replicas (int): Maximum no of machines to distribute the
            Vertex Batch Prediction job for horizontal scalability.


    Returns:
        None

    """

    # Create variables to ensure the same arguments are passed
    # into different components of the pipeline
    file_pattern = ""  # e.g. "files-*.csv", used as file pattern on storage
    time_column = "trip_start_timestamp"
    ingestion_table = "taxi_trips"
    table_suffix = "_tf_prediction"  # suffix to table names
    ingested_table = "ingested_data" + table_suffix

    # generate sql queries which are used in ingestion and preprocessing
    # operations
    queries_folder = pathlib.Path(__file__).parent / "queries"

    ingest_query = generate_query(
        queries_folder / "ingest.sql",
        source_dataset=f"{ingestion_project_id}.{ingestion_dataset_id}",
        source_table=ingestion_table,
        filter_column=time_column,
        filter_start_value=timestamp,
    )

    # data ingestion and preprocessing operations
    kwargs = dict(
        bq_client_project_id=project_id,
        destination_project_id=project_id,
        dataset_id=dataset_id,
        dataset_location=dataset_location,
        query_job_config=json.dumps(dict(write_disposition="WRITE_TRUNCATE")),
    )
    ingest = bq_query_to_table(
        query=ingest_query, table_id=ingested_table, **kwargs
    ).set_display_name("Ingest data")

    # data extraction to gcs
    data_for_prediction = (
        extract_bq_to_dataset(
            bq_client_project_id=project_id,
            source_project_id=project_id,
            dataset_id=dataset_id,
            table_name=ingested_table,
            dataset_location=dataset_location,
            extract_job_config=json.dumps(
                dict(destination_format="NEWLINE_DELIMITED_JSON")
            ),
        )
        .after(ingest)
        .set_display_name("Extract data to storage for prediction")
    )

    # lookup champion model
    champion_model = lookup_model(
        model_name=model_name,
        model_label=model_label,
        project_location=project_location,
        project_id=project_id,
        fail_on_model_not_found=True,
    ).set_display_name("Lookup champion model")

    # predict data
    batch_prediction = (
        model_batch_predict(
            model=champion_model.outputs["model"],
            job_display_name="my-tensorflow-batch-prediction-job",
            project_location=project_location,
            project_id=project_id,
            source_uri=data_for_prediction.outputs["dataset_gcs_uri"],
            destination_uri=data_for_prediction.outputs["dataset_gcs_prefix"],
            source_format="jsonl",
            destination_format="jsonl",
            machine_type=batch_prediction_machine_type,
            starting_replica_count=batch_prediction_min_replicas,
            max_replica_count=batch_prediction_max_replicas,
        )
        .after(ingest)
        .set_display_name("Vertex Batch Prediction for TF model")
    )

    wait_op = wait_gcp_resources(
        project_location=project_location,
        gcp_resources=batch_prediction.outputs["gcp_resources"],
    ).set_display_name("Wait for job completion")

    # load predictions into bigquery
    loaded_data = (
        load_dataset_to_bq(
            bq_client_project_id=project_id,
            destination_project_id=project_id,
            dataset_id=dataset_id,
            table_name="tensorflow_staging_predictions",
            gcs_source_uri=data_for_prediction.outputs["dataset_gcs_prefix"],
            dataset_location=dataset_location,
        )
        .after(wait_op)
        .set_display_name("Load predictions into Bigquery")
    )


def compile():
    """
    Uses the kfp compiler package to compile the pipeline function into a workflow yaml

    Args:
        None

    Returns:
        None
    """
    compiler.Compiler().compile(
        pipeline_func=tensorflow_pipeline,
        package_path="prediction.json",
        type_check=False,
    )


if __name__ == "__main__":
    compile()
