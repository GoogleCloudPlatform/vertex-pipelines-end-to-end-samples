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

from pipelines.utils.query import generate_query
from components import lookup_model, model_batch_predict


RESOURCE_SUFFIX = env.get("RESOURCE_SUFFIX", "default")
# set training-serving skew thresholds and emails to receive alerts:
ALERT_EMAILS = []
SKEW_THRESHOLDS = {"defaultSkewThreshold": {"value": 0.001}}
# or set different thresholds per feature:
# SKEW_THRESHOLDS = {"skewThresholds": {"payment_type": {"value": 0.001}}, ... }


@dsl.pipeline(name="turbo-prediction-pipeline")
def pipeline(
    project: str = env.get("VERTEX_PROJECT_ID"),
    location: str = env.get("VERTEX_LOCATION"),
    bq_location: str = env.get("BQ_LOCATION"),
    bq_source_uri: str = "bigquery-public-data.chicago_taxi_trips.taxi_trips",
    model_name: str = "xgb_regressor",
    dataset: str = "turbo_templates",
    timestamp: str = "2022-12-01 00:00:00",
    machine_type: str = "n2-standard-4",
    min_replicas: int = 3,
    max_replicas: int = 10,
):
    """
    Prediction pipeline which:
     1. Looks up the default model version (champion).
     2. Runs a batch prediction job with BigQuery as input and output
     3. Optionally monitors training-serving skew

    Args:
        project (str): project id of the Google Cloud project
        location (str): location of the Google Cloud project
        bq_location (str): location of dataset in BigQuery
        bq_source_uri (str): `<project>.<dataset>.<table>` of ingestion data in BigQuery
        model_name (str): name of model
        dataset (str): dataset id to store staging data & predictions in BigQuery
        timestamp (str): Optional. Empty or a specific timestamp in ISO 8601 format
            (YYYY-MM-DDThh:mm:ss.sss±hh:mm or YYYY-MM-DDThh:mm:ss).
            If any time part is missing, it will be regarded as zero
        machine_type (str): Machine type to be used for Vertex Batch
            Prediction. Example machine_types - n1-standard-4, n1-standard-16 etc.
        min_replicas (int): Minimum no of machines to distribute the
            Vertex Batch Prediction job for horizontal scalability
        max_replicas (int): Maximum no of machines to distribute the
            Vertex Batch Prediction job for horizontal scalability
    """

    queries_folder = pathlib.Path(__file__).parent / "queries"
    table = f"prep_prediction_{RESOURCE_SUFFIX}"

    prep_query = generate_query(
        queries_folder / "preprocessing.sql",
        source=bq_source_uri,
        location=bq_location,
        dataset=f"{project}.{dataset}",
        table=table,
        start_timestamp=timestamp,
    )

    prep_op = BigqueryQueryJobOp(
        project=project,
        location=bq_location,
        query=prep_query,
    ).set_display_name("Ingest & preprocess data")

    lookup_op = lookup_model(
        model_name=model_name,
        location=location,
        project=project,
        fail_on_model_not_found=True,
    ).set_display_name("Look up champion model")

    (
        model_batch_predict(
            model=lookup_op.outputs["model"],
            job_display_name="turbo-template-predict-job",
            location=location,
            project=project,
            source_uri=f"bq://{project}.{dataset}.{table}",
            destination_uri=f"bq://{project}.{dataset}",
            source_format="bigquery",
            destination_format="bigquery",
            instance_config={
                "instanceType": "object",
            },
            machine_type=machine_type,
            starting_replica_count=min_replicas,
            max_replica_count=max_replicas,
            monitoring_training_dataset=lookup_op.outputs["training_dataset"],
            monitoring_alert_email_addresses=ALERT_EMAILS,
            monitoring_skew_config=SKEW_THRESHOLDS,
        )
        .after(prep_op)
        .set_display_name("Run prediction job")
    )
