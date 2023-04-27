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
from pathlib import Path
from typing import List, NamedTuple


@component(
    base_image="python:3.7",
    packages_to_install=[
        "google-cloud-aiplatform>=1.24.0",
        "google_cloud_pipeline_components>=1.0.0",
    ],
    output_component_file=str(Path(__file__).with_suffix(".yaml")),
)
def model_batch_predict(
    model: Input[Model],
    job_display_name: str,
    project_location: str,
    project_id: str,
    bigquery_source_input_uri: str,
    bigquery_destination_output_uri: str,
    bigquery_source_training_uri: str,
    machine_type: str = "n1-standard-2",
    starting_replica_count: int = 1,
    max_replica_count: int = 1,
    alert_email_addresses: List[str] = None,
) -> NamedTuple("Outputs", [("gcp_resources", str)]):
    """
    Fetch a model given a model name (display name) and export to GCS.

    Args:
        model (Output[Model]): output model to be exported to GCS
        project_location (str): location of the Google Cloud project. Defaults to None.
        project_id (str): project id of the Google Cloud project. Defaults to None.
    Returns:
        None
    """

    import logging
    from google.protobuf.json_format import ParseDict, MessageToJson
    from google.cloud.aiplatform_v1beta1.services.job_service import JobServiceClient
    from google.cloud.aiplatform_v1beta1.types import BatchPredictionJob
    from google_cloud_pipeline_components.proto.gcp_resources_pb2 import GcpResources

    api_endpoint = f"{project_location}-aiplatform.googleapis.com"
    if alert_email_addresses is None:
        alert_email_addresses = []
    message = {
        "displayName": job_display_name,
        "model": model.metadata["resourceName"],
        "inputConfig": {
            "instancesFormat": "bigquery",
            # gcs_source=GcsSource(uris=[...])
            "bigquerySource": {"inputUri": bigquery_source_input_uri},
        },
        "outputConfig": {
            "predictionsFormat": "bigquery",
            "bigqueryDestination": {"output_uri": bigquery_destination_output_uri}
            # gcs_destination=GcsDestination(output_uri_prefix=...),
        },
        "dedicated_resources": {
            "machineSpec": {"machineType": machine_type},
            "startingReplicaCount": starting_replica_count,
            "maxReplicaCount": max_replica_count,
        },
        "model_monitoring_config": {
            "alertConfig": {"emailAlertConfig": {"userEmails": alert_email_addresses}},
            "objectiveConfigs": [
                {
                    "trainingDataset": {
                        "bigquerySource": {"inputUri": bigquery_source_training_uri},
                    },
                    "trainingPredictionSkewDetectionConfig": {
                        "defaultSkewThreshold": {"value": 0.001}
                    },
                }
            ],
        },
    }
    request = ParseDict(message, BatchPredictionJob()._pb)

    logging.info(f"Submitting batch prediction job: {job_display_name}")
    client = JobServiceClient(client_options={"api_endpoint": api_endpoint})
    response = client.create_batch_prediction_job(
        parent=f"projects/{project_id}/locations/{project_location}",
        batch_prediction_job=request,
    )
    logging.info(f"Submitted batch prediction job: {response.name}")

    # return GCP resource for Vertex AI UI integration
    batch_job_resources = GcpResources()
    dr = batch_job_resources.resources.add()
    dr.resource_type = "BatchPredictionJob"
    dr.resource_uri = response.name
    gcp_resources = MessageToJson(batch_job_resources)

    return (gcp_resources,)
