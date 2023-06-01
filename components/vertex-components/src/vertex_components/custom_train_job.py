# Copyright 2022 Google LLC
from typing import List, Dict, NamedTuple

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from kfp.v2.dsl import Input, component, Metrics, Output, Artifact, Dataset


@component(
    base_image="python:3.7",
    packages_to_install=[
        "google-cloud-aiplatform==1.24.1",
        "google-cloud-pipeline-components==1.0.42",
    ],
)
def custom_train_job(
    train_script_uri: str,
    train_data: Input[Dataset],
    valid_data: Input[Dataset],
    test_data: Input[Dataset],
    project_id: str,
    project_location: str,
    model_display_name: str,
    train_container_uri: str,
    serving_container_uri: str,
    model: Output[Artifact],
    metrics: Output[Metrics],
    staging_bucket: str,
    requirements: List[str] = None,
    job_name: str = None,
    hparams: Dict[str, str] = None,
    replica_count: int = 1,
    machine_type: str = "n1-standard-4",
    accelerator_type: str = "ACCELERATOR_TYPE_UNSPECIFIED",
    accelerator_count: int = 0,
    parent_model: str = None,
) -> NamedTuple("Outputs", [("gcp_resources", str)]):
    """Run a custom training job using a training script.

    The provided script will be invoked by passing the following command-line arguments:

    ```
    train.py \
        --train_data <train_data.path> \
        --valid_data <valid_data.path> \
        --test_data <test_data.path> \
        --metrics <metrics.path> \
        --hparams json.dumps(<hparams>)
    ```

    Ensure that your train script can read these arguments and outputs metrics
    to the provided path and the model to the correct path based on:
    https://cloud.google.com/vertex-ai/docs/training/code-requirements.

    Args:
        train_script_uri (str): gs:// uri to python train script. See:
            https://cloud.google.com/vertex-ai/docs/training/code-requirements.
        train_data (Dataset): Training data (passed as an argument to train script)
        valid_data (Dataset): Validation data (passed as an argument to train script)
        test_data (Dataset): Test data (passed as an argument to train script).
        staging_bucket (str): Staging bucket for CustomTrainingJob.
        project_location (str): location of the Google Cloud project.
        project_id (str): project id of the Google Cloud project.
        model_display_name (str): Name of the new trained model version.
        train_container_uri (str): Container URI for running train script.
        serving_container_uri (str): Container URI for deploying the output model.
        model (Model): Trained model output.
        metrics (Metrics): Output metrics of trained model.
        requirements (List[str]): Additional python dependencies for training script.
        job_name (str): Name of training job.
        hparams (Dict[str, str]): Hyperparameters (passed as a JSON serialised argument
            to train script)
        replica_count (int): Number of replicas (increase for distributed training).
        machine_type (str): Machine type of compute.
        accelerator_type (str): Accelerator type (change for GPU support).
        accelerator_count (str): Accelerator count (increase for GPU cores).
        parent_model (str): Resource URI of existing parent model (optional). If `None`,
            a new model will be uploaded. Otherwise, a new model version for the parent
            model will be uploaded.
    Returns:
        parent_model (str): Resource URI of the parent model (empty string if the
            trained model is the first model version of its kind).
        NamedTuple: gcp_resources for Vertex AI UI integration.
    """
    import json
    import logging
    import os.path
    import time
    import google.cloud.aiplatform as aip
    from google_cloud_pipeline_components.proto.gcp_resources_pb2 import GcpResources
    from google.protobuf.json_format import MessageToJson

    logging.info(f"Using train script: {train_script_uri}")
    script_path = "/gcs/" + train_script_uri[5:]
    if not os.path.exists(script_path):
        raise ValueError(
            "Train script was not found. "
            f"Check if the path is correct: {train_script_uri}"
        )

    job = aip.CustomTrainingJob(
        project=project_id,
        location=project_location,
        staging_bucket=staging_bucket,
        display_name=job_name if job_name else f"Custom job {int(time.time())}",
        script_path=script_path,
        container_uri=train_container_uri,
        requirements=requirements,
        model_serving_container_image_uri=serving_container_uri,
    )
    cmd_args = [
        f"--train_data={train_data.path}",
        f"--valid_data={valid_data.path}",
        f"--test_data={test_data.path}",
        f"--metrics={metrics.path}",
        f"--hparams={json.dumps(hparams if hparams else {})}",
    ]
    uploaded_model = job.run(
        model_display_name=model_display_name,
        parent_model=parent_model,
        is_default_version=(not parent_model),
        args=cmd_args,
        replica_count=replica_count,
        machine_type=machine_type,
        accelerator_type=accelerator_type,
        accelerator_count=accelerator_count,
    )

    resource_name = f"{uploaded_model.resource_name}@{uploaded_model.version_id}"
    model.metadata["resourceName"] = resource_name
    model.metadata["containerSpec"] = {"imageUri": serving_container_uri}
    model.uri = uploaded_model.uri
    model.TYPE_NAME = "google.VertexModel"

    with open(metrics.path, "r") as fp:
        parsed_metrics = json.load(fp)

    logging.info(parsed_metrics)
    for k, v in parsed_metrics.items():
        if type(v) is float:
            metrics.log_metric(k, v)

    # return GCP resource for Vertex AI UI integration
    custom_job_name = job.to_dict()["trainingTaskMetadata"]["backingCustomJob"]
    custom_train_job_resources = GcpResources()
    ctr = custom_train_job_resources.resources.add()
    ctr.resource_type = "CustomJob"
    ctr.resource_uri = custom_job_name
    gcp_resources = MessageToJson(custom_train_job_resources)
    return (gcp_resources,)
