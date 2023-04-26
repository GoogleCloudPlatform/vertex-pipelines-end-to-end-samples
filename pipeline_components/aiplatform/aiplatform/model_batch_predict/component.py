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
from typing import List


@component(
    base_image="python:3.7",
    packages_to_install=["google-cloud-aiplatform==1.24.1"],
    output_component_file=str(Path(__file__).with_suffix(".yaml")),
)
def export_model(
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
) -> None:
    """
    Fetch a model given a model name (display name) and export to GCS.

    Args:
        model (Output[Model]): output model to be exported to GCS
        project_location (str): location of the Google Cloud project. Defaults to None.
        project_id (str): project id of the Google Cloud project. Defaults to None.
    Returns:
        None
    """

    import google.cloud.aiplatform_v1beta1 as tmp

    print(tmp.__version__)

    import time
    import logging
    from google.cloud.aiplatform_v1beta1.services.job_service import JobServiceClient
    from google.cloud.aiplatform_v1beta1.types import (
        BatchDedicatedResources,
        BatchPredictionJob,
        BigQuerySource,
        MachineSpec,
        ModelMonitoringAlertConfig,
        ModelMonitoringConfig,
        ModelMonitoringObjectiveConfig,
        ThresholdConfig,
        BigQueryDestination,
        GetBatchPredictionJobRequest,
    )
    from google.cloud.aiplatform_v1beta1.types.job_state import JobState

    api_endpoint = f"{project_location}-aiplatform.googleapis.com"

    alert_config = None
    if alert_email_addresses is not None:
        alert_config = ModelMonitoringAlertConfig(
            email_alert_config=ModelMonitoringAlertConfig.EmailAlertConfig(
                user_emails=[alert_email_addresses]
            )
        )

    skew_detection_config = (
        ModelMonitoringObjectiveConfig.TrainingPredictionSkewDetectionConfig(
            default_skew_threshold=ThresholdConfig(value=0.001),
        )
    )

    job_request = BatchPredictionJob(
        display_name=job_display_name,
        model=model.metadata["resourceName"],
        input_config=BatchPredictionJob.InputConfig(
            instances_format="bigquery",
            bigquery_source=BigQuerySource(input_uri=bigquery_source_input_uri),
        ),
        output_config=BatchPredictionJob.OutputConfig(
            predictions_format="bigquery",
            bigquery_destination=BigQueryDestination(
                output_uri=bigquery_destination_output_uri
            ),
        ),
        dedicated_resources=BatchDedicatedResources(
            machine_spec=MachineSpec(machine_type=machine_type),
            starting_replica_count=starting_replica_count,
            max_replica_count=max_replica_count,
        ),
        model_monitoring_config=ModelMonitoringConfig(
            alert_config=alert_config,
            objective_configs=[
                ModelMonitoringObjectiveConfig(
                    training_dataset=ModelMonitoringObjectiveConfig.TrainingDataset(
                        bigquery_source=BigQuerySource(
                            input_uri=bigquery_source_training_uri
                        ),
                    ),
                    training_prediction_skew_detection_config=skew_detection_config,
                )
            ],
        ),
    )

    logging.info(f"Submitting batch prediction job: {job_display_name}")
    client = JobServiceClient(client_options={"api_endpoint": api_endpoint})
    job_response = client.create_batch_prediction_job(
        parent=f"projects/{project_id}/locations/{project_location}",
        batch_prediction_job=job_request,
    )
    logging.info(f"Submitted batch prediction job: {job_response.name}")

    states = [
        JobState.JOB_STATE_SUCCEEDED,
        JobState.JOB_STATE_FAILED,
        JobState.JOB_STATE_CANCELLED,
        JobState.JOB_STATE_EXPIRED,
    ]
    job_status_request = GetBatchPredictionJobRequest(name=job_response.name)
    state = client.get_batch_prediction_job(request=job_status_request).state

    while state not in states:
        logging.info(f"Batch prediction job state: {state}, waiting for 10s...")
        time.sleep(10)
        state = client.get_batch_prediction_job(request=job_status_request).state
