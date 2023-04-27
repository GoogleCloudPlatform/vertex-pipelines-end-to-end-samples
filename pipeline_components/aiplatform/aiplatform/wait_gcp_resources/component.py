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

from kfp.v2.dsl import component
from pathlib import Path


@component(
    base_image="python:3.7",
    packages_to_install=[
        "google-cloud-aiplatform>=1.24.0",
        "google_cloud_pipeline_components>=1.0.0",
    ],
    output_component_file=str(Path(__file__).with_suffix(".yaml")),
)
def wait_gcp_resources(
    project_location: str,
    gcp_resources: str,
) -> None:
    """
    Fetch a model given a model name (display name) and export to GCS.

    Args:
        project_location (str): location of the Google Cloud project. Defaults to None.
        gcp_resources (str): serialised GCP resources including a batch prediction job
    Returns:
        None
    """

    import logging
    import time
    from functools import partial

    from google.cloud.aiplatform_v1beta1.services.job_service import JobServiceClient
    from google.cloud.aiplatform_v1beta1.types import GetBatchPredictionJobRequest
    from google.cloud.aiplatform_v1beta1.types.job_state import JobState
    from google_cloud_pipeline_components.container.v1.gcp_launcher.utils import (
        error_util,
    )
    from google_cloud_pipeline_components.container.utils import execution_context
    from google_cloud_pipeline_components.proto.gcp_resources_pb2 import GcpResources
    from google.protobuf.json_format import Parse

    _POLLING_INTERVAL_IN_SECONDS = 20
    _CONNECTION_ERROR_RETRY_LIMIT = 5
    _JOB_SUCCESSFUL_STATES = [
        JobState.JOB_STATE_SUCCEEDED,
    ]
    _JOB_CANCELLED_STATE = (JobState.JOB_STATE_CANCELLED,)
    _JOB_FAILED_STATES = [
        JobState.JOB_STATE_FAILED,
        _JOB_CANCELLED_STATE,
        JobState.JOB_STATE_EXPIRED,
    ]
    _JOB_TERMINATED_STATES = _JOB_SUCCESSFUL_STATES + _JOB_FAILED_STATES

    def _send_cancel_request(client: JobServiceClient, batch_job_uri: str):
        logging.info("Sending BatchPredictionJob cancel request")
        client.cancel_batch_prediction_job(name=batch_job_uri)

    api_endpoint = f"{project_location}-aiplatform.googleapis.com"
    client = JobServiceClient(client_options={"api_endpoint": api_endpoint})
    input_gcp_resources = Parse(gcp_resources, GcpResources())

    if len(input_gcp_resources.resources) != 1:
        raise ValueError(
            f"Invalid payload: {gcp_resources}. "
            "Wait component support waiting on only one resource at this moment."
        )

    if input_gcp_resources.resources[0].resource_type != "BatchPredictionJob":
        raise ValueError(
            f"Invalid payload: {gcp_resources}. "
            "Wait component only support waiting on Dataflow job at this moment."
        )

    batch_job_uri = input_gcp_resources.resources[0].resource_uri

    with execution_context.ExecutionContext(
        on_cancel=partial(
            _send_cancel_request,
            api_endpoint,
            batch_job_uri,
        )
    ):
        retry_count = 0
        while True:
            try:
                job_status_request = GetBatchPredictionJobRequest(name=batch_job_uri)
                job_state = client.get_batch_prediction_job(
                    request=job_status_request
                ).state
                retry_count = 0
            except ConnectionError as err:
                retry_count += 1
                if retry_count <= _CONNECTION_ERROR_RETRY_LIMIT:
                    logging.warning(
                        f"ConnectionError ({err}) encountered when polling job: "
                        f"{batch_job_uri}. Retrying."
                    )
                else:
                    error_util.exit_with_internal_error(
                        f"Request failed after {_CONNECTION_ERROR_RETRY_LIMIT} retries."
                    )

            if job_state in _JOB_SUCCESSFUL_STATES:
                logging.info(
                    f"GetBatchPredictionJobRequest response state={job_state}. "
                    "Job completed"
                )
                break
            elif job_state in _JOB_TERMINATED_STATES:
                raise RuntimeError(
                    "Job {} failed with error state: {}.".format(
                        batch_job_uri, job_state
                    )
                )
            else:
                logging.info(
                    f"Job {batch_job_uri} is in a non-final state {job_state}. "
                    "Waiting for {_POLLING_INTERVAL_IN_SECONDS} seconds for next poll."
                )
                time.sleep(_POLLING_INTERVAL_IN_SECONDS)
