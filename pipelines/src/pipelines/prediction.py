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

from pipelines.utils.load_config import load_variables
from pipelines.utils.query import generate_query
from components import (
    create_model_monitor,
    deploy_model,
    lookup_model,
    model_batch_predict,
    predict_on_endpoint,
    run_model_monitoring_job,
    undeploy_model,
)


prediction_config = load_variables()
# Prefer env so CI (e.g. e2e-test) can override YAML with COMMIT_SHA.
RESOURCE_SUFFIX = env.get("RESOURCE_SUFFIX") or prediction_config.get(
    "resource_suffix", "default"
)

ALERT_EMAILS = prediction_config.get("alert_emails", [])
NOTIFICATION_CHANNELS = prediction_config.get("notification_channels", [])
SKEW_THRESHOLDS = prediction_config.get("monitoring", {}).get(
    "skew_thresholds", {"defaultSkewThreshold": {"value": 0.001}}
)

PREDICTION_TYPE = prediction_config.get("prediction_type", "batch")
ENDPOINT_NAME = prediction_config.get("endpoint_name", "turbo-prediction-endpoint")
UNDEPLOY_ENDPOINT = prediction_config.get("undeploy_endpoint", True)

_DEFAULT_MONITORED_FEATURES = {
    "dayofweek": "float",
    "hourofday": "float",
    "trip_distance": "float",
    "trip_miles": "float",
    "trip_seconds": "float",
    "payment_type": "categorical",
    "company": "categorical",
}
_monitoring = prediction_config.get("monitoring", {})
# Endpoint (online) Model Monitoring v2 only. Batch uses v1 skew below.
MONITORING_ENABLED = _monitoring.get("enable", False)
DEFAULT_DRIFT_THRESHOLD = _monitoring.get("default_drift_threshold", 0.3)
MONITORED_FEATURES = _monitoring.get("monitored_features", _DEFAULT_MONITORED_FEATURES)
NOTIFICATION_EMAILS = _monitoring.get("notification_emails") or ALERT_EMAILS
LOGGING_SAMPLING_RATE = _monitoring.get("logging_sampling_rate", 0.3)


@dsl.pipeline(name="turbo-prediction-pipeline")
def pipeline(
    project: str = env.get("VERTEX_PROJECT_ID"),
    location: str = prediction_config.get("vertex_location", "europe-west2"),
    bq_location: str = prediction_config.get("bq_location", "europe-west2"),
    bq_source_uri: str = (
        f"{env.get('VERTEX_PROJECT_ID')}."
        f"{prediction_config.get('bq_dataset_id', 'ml_dataset')}."
        f"{prediction_config.get('bq_table_id', 'taxi_trips')}"
    ),
    model_name: str = prediction_config.get("model_name", "xgb_regressor"),
    dataset: str = prediction_config.get("bq_dataset_id", "turbo_templates"),
    timestamp: str = "2013-08-01 00:00:00",
    machine_type: str = prediction_config.get("machine_type", "n2-standard-4"),
    min_replicas: int = 3,
    max_replicas: int = 10,
    endpoint_name: str = ENDPOINT_NAME,
    service_account: str = env.get("VERTEX_SA_EMAIL"),
):
    """
    Prediction pipeline which:
     1. Looks up the default model version (champion).
     2. Either runs a batch prediction job (prediction_type=batch) or deploys
        the model to an endpoint and smoke-tests it (prediction_type=endpoint).
        When prediction_type=endpoint, undeploy_endpoint in variables.yml
        controls whether the model is undeployed afterward (default: true).

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
        endpoint_name (str): Display name for the Vertex AI endpoint
            (only used when prediction_type=endpoint)
        service_account (str): Service account email for the deployed model
            (only used when prediction_type=endpoint)
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

    if PREDICTION_TYPE == "endpoint":
        deploy_op = (
            deploy_model(
                vertex_model=lookup_op.outputs["model"],
                project=project,
                location=location,
                endpoint_name=endpoint_name,
                service_account=service_account,
                machine_type=machine_type,
                min_replica_count=min_replicas,
                max_replica_count=max_replicas,
                enable_request_response_logging=MONITORING_ENABLED,
                logging_sampling_rate=LOGGING_SAMPLING_RATE,
            )
            .after(prep_op)
            .set_display_name("Deploy model to endpoint")
        )

        predict_op = predict_on_endpoint(
            endpoint_id=deploy_op.outputs["endpoint_id"],
            project=project,
            location=location,
        ).set_display_name("Smoke-test predictions")

        undeploy_after = predict_op
        if MONITORING_ENABLED:
            monitor_op = create_model_monitor(
                vertex_model=lookup_op.outputs["model"],
                project=project,
                location=location,
                display_name=f"{endpoint_name}-monitor",
                monitored_features=MONITORED_FEATURES,
            ).set_display_name("Create model monitor")

            undeploy_after = (
                run_model_monitoring_job(
                    project=project,
                    location=location,
                    model_monitor_name=monitor_op.outputs["model_monitor_name"],
                    training_dataset_gcs_uri=lookup_op.outputs[
                        "training_dataset_gcs_uri"
                    ],
                    target_bq_table_uri=deploy_op.outputs["logging_bq_table"],
                    endpoint_id=deploy_op.outputs["endpoint_id"],
                    job_display_name=f"{endpoint_name}-monitoring",
                    monitored_features=MONITORED_FEATURES,
                    default_drift_threshold=DEFAULT_DRIFT_THRESHOLD,
                    notification_emails=NOTIFICATION_EMAILS,
                )
                .after(predict_op)
                .set_display_name("Run monitoring analysis")
            )

        undeploy_model(
            project=project,
            location=location,
            endpoint_id=deploy_op.outputs["endpoint_id"],
            delete_endpoint_if_empty=True,
        ).after(undeploy_after).set_display_name("Undeploy model")
        if UNDEPLOY_ENDPOINT:
            undeploy_model(
                project=project,
                location=location,
                endpoint_id=deploy_op.outputs["endpoint_id"],
                delete_endpoint_if_empty=True,
            ).after(predict_op).set_display_name("Undeploy model")

    else:
        (
            model_batch_predict(
                model=lookup_op.outputs["model"],
                job_display_name="turbo-template-predict-job",
                location=location,
                project=project,
                source_uri="bq://" + f"{project}.{dataset}.{table}",
                destination_uri="bq://" + f"{project}.{dataset}",
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
                notification_channels=NOTIFICATION_CHANNELS,
                monitoring_skew_config=SKEW_THRESHOLDS,
            )
            .after(prep_op)
            .set_display_name("Model batch prediction")
        )
