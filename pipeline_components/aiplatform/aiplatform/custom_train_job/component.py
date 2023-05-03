# Copyright 2022 Google LLC
from typing import NamedTuple, List, Dict

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
from pathlib import Path


@component(
    base_image="python:3.7",
    packages_to_install=["google-cloud-aiplatform==1.24.1"],
    output_component_file=str(Path(__file__).with_suffix(".yaml")),
)
def custom_train_job(
    task: Input[Artifact],
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
    requirements: List[str] = None,
    job_name: str = None,
    hparams: Dict[str, str] = None,
    replica_count: int = 1,
    machine_type: str = "n1-standard-4",
    accelerator_type: str = "ACCELERATOR_TYPE_UNSPECIFIED",
    accelerator_count: int = 0,
) -> NamedTuple("Outputs", [("parent_model", str)]):
    """Run a custom training job using a task (e.g. training) script.

    The provided task will be invoked by passing the following command-line arguments:

    ```
    train_xgb_model.py \
        --train_data <train_data.path> \
        --valid_data <valid_data.path> \
        --test_data <test_data.path> \
        --metrics <metrics.path> \
        --hparams json.dumps(<hparams>)
    ```

    Ensure that your task can read these arguments and outputs metrics to the provided
    path and the model to the correct path based on:
    https://cloud.google.com/vertex-ai/docs/training/code-requirements.

    Args:
        task (Artifact): Python task script. See:
            https://cloud.google.com/vertex-ai/docs/training/code-requirements.
        train_data (Dataset): Training data (passed as an argument to task script)
        valid_data (Dataset): Validation data (passed as an argument to task script)
        test_data (Dataset): Test data (passed as an argument to task script).
        project_location (str): location of the Google Cloud project.
        project_id (str): project id of the Google Cloud project.
        model_display_name (str): Name of the new trained model version.
        train_container_uri (str): Container URI for running task script.
        serving_container_uri (str): Container URI for deploying the output model.
        model (Model): Trained model output.
        metrics (Metrics): Output metrics of trained model.
        requirements (List[str]): Additional python dependencies for training script.
        job_name (str): Name of training job.
        hparams (Dict[str, str]): Hyperparameters (passed as a JSON serialised argument
            to task script)
        replica_count (int): Number of replicas (increase for distributed tasks).
        machine_type (string): Machine type of compute.
        accelerator_type (string): Accelerator type (change for GPU support).
        accelerator_count (string): Accelerator count (increase for GPU cores).

    Returns:
        parent_model (str): Resource URI of the parent model (empty string if the
            trained model is the first model version of its kind).
    """
    import json
    import logging
    import time
    import google.cloud.aiplatform as aip

    logging.info(f"Checking if parent model with name {model_display_name} exists")
    models = aip.Model.list(filter=f"displayName={model_display_name}")

    # check if a model with the same name already exists
    if len(models) == 0:
        logging.info("No parent model found.")
        parent_model = None
        is_default_version = True
    elif len(models) == 1:
        parent_model = models[0].resource_name
        is_default_version = False
        logging.info(f"Parent model found: {parent_model}")
    else:
        raise RuntimeError(
            f"Multiple models with name {model_display_name} were found."
        )

    job = aip.CustomTrainingJob(
        project=project_id,
        location=project_location,
        staging_bucket="gs://dt-turbo-templates-dev-pl-root",
        display_name=job_name if job_name else f"Custom job {int(time.time())}",
        script_path=task.path,
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
        is_default_version=is_default_version,
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

    # KFP doesn't support type None
    if parent_model is None:
        parent_model = ""

    return (parent_model,)
