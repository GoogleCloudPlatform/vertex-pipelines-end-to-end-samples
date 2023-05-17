# Copyright 2022 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from kfp.v2.dsl import Input, Model, component
from typing import List, NamedTuple


@component(
    base_image="python:3.7",
    packages_to_install=[
        "google-cloud-aiplatform==1.24.1",
        "google-cloud-pipeline-components==1.0.33",
    ],
)
def model_batch_predict(
    model: Input[Model],
    job_display_name: str,
    project_location: str,
    project_id: str,
    source_uri: str,
    destination_uri: str,
    source_format: str,
    destination_format: str,
    machine_type: str = "n1-standard-2",
    starting_replica_count: int = 1,
    max_replica_count: int = 1,
    monitoring_training_dataset: dict = None,
    monitoring_alert_email_addresses: List[str] = None,
    monitoring_skew_config: dict = None,
    instance_config: dict = None,
) -> NamedTuple("Outputs", [("gcp_resources", str)]):
    """
    Trigger a batch prediction job and enable monitoring.

    Args:
        model (Input[Model]): Input model to use for calculating predictions.
        job_display_name: Name of the batch prediction job.
        project_location (str): location of the Google Cloud project. Defaults to None.
        project_id (str): project id of the Google Cloud project. Defaults to None.
        source_uri (str): bq:// URI or a list of gcs:// URIs to read input instances.
        destination_uri (str): bq:// or gs:// URI to store output predictions.
        source_format (str): E.g. "bigquery", "jsonl", "csv". See:
            https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform_v1beta1.types.BatchPredictionJob.InputConfig
        destination_format (str): E.g. "bigquery", "jsonl", "csv". See:
            https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform_v1beta1.types.BatchPredictionJob.OutputConfig
        machine_type (str): Machine type.
        starting_replica_count (int): Starting replica count.
        max_replica_count (int): Max replicat count.
        monitoring_skew_config (dict): Configuration of training-serving skew. See:
            https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform_v1beta1.types.ModelMonitoringObjectiveConfig.TrainingPredictionSkewDetectionConfig
        monitoring_alert_email_addresses (List[str]):
            Email addresses to send alerts to (optional).
        monitoring_training_dataset (dict): Metadata of training dataset. See:
            https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform_v1beta1.types.ModelMonitoringObjectiveConfig.TrainingDataset
        instance_config (dict): Configuration defining how to transform batch prediction
            input instances to the instances that the Model accepts. See:
            https://cloud.google.com/vertex-ai/docs/reference/rest/v1beta1/projects.locations.batchPredictionJobs#instanceconfig
    Returns:
        NamedTuple: gcp_resources for Vertex AI UI integration.
    """

    import logging
    import time

    from functools import partial
    from google.protobuf.json_format import ParseDict, MessageToJson
    from google.cloud.aiplatform_v1beta1.services.job_service import JobServiceClient
    from google.cloud.aiplatform_v1beta1.types import (
        BatchPredictionJob,
        GetBatchPredictionJobRequest,
    )
    from google.cloud.aiplatform_v1beta1.types.job_state import JobState
    from google_cloud_pipeline_components.container.v1.gcp_launcher.utils import (
        error_util,
    )
    from google_cloud_pipeline_components.container.utils import execution_context
    from google_cloud_pipeline_components.proto.gcp_resources_pb2 import GcpResources

    def send_cancel_request(client: JobServiceClient, batch_job_uri: str):
        logging.info("Sending BatchPredictionJob cancel request")
        client.cancel_batch_prediction_job(name=batch_job_uri)

    def is_job_successful(job_state: JobState) -> bool:
        _JOB_SUCCESSFUL_STATES = [
            JobState.JOB_STATE_SUCCEEDED,
        ]
        _JOB_FAILED_STATES = [
            JobState.JOB_STATE_FAILED,
            JobState.JOB_STATE_CANCELLED,
            JobState.JOB_STATE_EXPIRED,
        ]

        if job_state in _JOB_SUCCESSFUL_STATES:
            logging.info(
                f"GetBatchPredictionJobRequest response state={job_state}. "
                "Job completed"
            )
            return True
        elif job_state in _JOB_FAILED_STATES:
            raise RuntimeError(
                "Job {} failed with error state: {}.".format(response.name, job_state)
            )
        else:
            logging.info(f"Job {response.name} is in a non-final state {job_state}.")
        return False

    _POLLING_INTERVAL_IN_SECONDS = 20
    _CONNECTION_ERROR_RETRY_LIMIT = 5

    api_endpoint = f"{project_location}-aiplatform.googleapis.com"

    input_config = {"instancesFormat": source_format}
    output_config = {"predictionsFormat": destination_format}
    if source_format == "bigquery" and destination_format == "bigquery":
        input_config["bigquerySource"] = {"inputUri": source_uri}
        output_config["bigqueryDestination"] = {"outputUri": destination_uri}
    else:
        input_config["gcsSource"] = {"uris": [source_uri]}
        output_config["gcsDestination"] = {"outputUriPrefix": destination_uri}

    message = {
        "displayName": job_display_name,
        "model": model.metadata["resourceName"],
        "inputConfig": input_config,
        "outputConfig": output_config,
        "dedicatedResources": {
            "machineSpec": {"machineType": machine_type},
            "startingReplicaCount": starting_replica_count,
            "maxReplicaCount": max_replica_count,
        },
    }

    if instance_config:
        message["instanceConfig"] = instance_config

    if monitoring_training_dataset and monitoring_skew_config:
        logging.info("Adding monitoring config to request")
        if not monitoring_alert_email_addresses:
            monitoring_alert_email_addresses = []

        message["modelMonitoringConfig"] = {
            "alertConfig": {
                "emailAlertConfig": {"userEmails": monitoring_alert_email_addresses}
            },
            "objectiveConfigs": [
                {
                    "trainingDataset": monitoring_training_dataset,
                    "trainingPredictionSkewDetectionConfig": monitoring_skew_config,
                }
            ],
        }

    request = ParseDict(message, BatchPredictionJob()._pb)

    logging.info(f"Submitting batch prediction job: {job_display_name}")
    logging.info(request)
    client = JobServiceClient(client_options={"api_endpoint": api_endpoint})
    response = client.create_batch_prediction_job(
        parent=f"projects/{project_id}/locations/{project_location}",
        batch_prediction_job=request,
    )
    logging.info(f"Submitted batch prediction job: {response.name}")

    with execution_context.ExecutionContext(
        on_cancel=partial(
            send_cancel_request,
            api_endpoint,
            response.name,
        )
    ):
        retry_count = 0
        while True:
            try:
                job_status_request = GetBatchPredictionJobRequest(
                    {"name": response.name}
                )
                job_state = client.get_batch_prediction_job(
                    request=job_status_request
                ).state
                retry_count = 0
            except ConnectionError as err:
                retry_count += 1
                if retry_count <= _CONNECTION_ERROR_RETRY_LIMIT:
                    logging.warning(
                        f"ConnectionError ({err}) encountered when polling job: "
                        f"{response.name}. Retrying."
                    )
                else:
                    error_util.exit_with_internal_error(
                        f"Request failed after {_CONNECTION_ERROR_RETRY_LIMIT} retries."
                    )
            if is_job_successful(job_state):
                break
            logging.info(
                f"Waiting for {_POLLING_INTERVAL_IN_SECONDS} seconds for next poll."
            )
            time.sleep(_POLLING_INTERVAL_IN_SECONDS)

    # return GCP resource for Vertex AI UI integration
    batch_job_resources = GcpResources()
    dr = batch_job_resources.resources.add()
    dr.resource_type = "BatchPredictionJob"
    dr.resource_uri = response.name
    gcp_resources = MessageToJson(batch_job_resources)

    return (gcp_resources,)
