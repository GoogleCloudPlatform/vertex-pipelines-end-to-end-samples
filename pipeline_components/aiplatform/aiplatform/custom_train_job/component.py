# Copyright 2022 Google LLC
from typing import NamedTuple

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from kfp.v2.dsl import Input, component, Metrics, Output, Artifact
from pathlib import Path


# TODO change to prebuilt container
# TODO update test data
# TODO update pipeline id


@component(
    base_image="python:3.7",
    packages_to_install=["google-cloud-aiplatform==1.24.1"],
    output_component_file=str(Path(__file__).with_suffix(".yaml")),
)
def custom_train_job(
    task: Input[Artifact],
    project_id: str,
    project_location: str,
    model: Output[Artifact],
    metrics: Output[Metrics],
) -> NamedTuple("Outputs", [("parent_model", str)]):
    import json
    import logging
    import google.cloud.aiplatform as aip

    TRAIN_VERSION = "tf-cpu.2-9"
    DEPLOY_VERSION = "tf2-cpu.2-9"

    TRAIN_IMAGE = "us-docker.pkg.dev/vertex-ai/training/{}:latest".format(TRAIN_VERSION)
    DEPLOY_IMAGE = "us-docker.pkg.dev/vertex-ai/prediction/{}:latest".format(
        DEPLOY_VERSION
    )

    JOB_NAME = "custom_job_unique"

    # CMDARGS = [
    #     "--epochs=1",
    #     "--steps=100",
    #     "--distribute=single",
    #     f"--model={model.path}"
    #     f"--metrics={metrics.path}"
    # ]
    #
    # job = CustomJob.from_local_script(
    #     project=project_id,
    #     location=project_location,
    #     staging_bucket="gs://dt-turbo-templates-dev-pl-root",
    #     display_name=JOB_NAME,
    #     script_path=task.path,
    #     container_uri=TRAIN_IMAGE,
    #     requirements=["tensorflow_datasets"],
    #     replica_count=1,
    #     machine_type="n1-standard-4",
    #     args=CMDARGS
    # )
    #
    # job.run()

    job = aip.CustomTrainingJob(
        project=project_id,
        location=project_location,
        staging_bucket="gs://dt-turbo-templates-dev-pl-root",
        display_name=JOB_NAME,
        script_path=task.path,
        container_uri=TRAIN_IMAGE,
        requirements=["tensorflow_datasets"],
        model_serving_container_image_uri=DEPLOY_IMAGE,
    )
    logging.info(job)

    MODEL_DISPLAY_NAME = "cifar10_unique"
    CMDARGS = [
        "--epochs=1",
        "--steps=100",
        "--distribute=single",
        f"--metrics={metrics.path}",
    ]
    logging.info(f"Checking if parent model with name {MODEL_DISPLAY_NAME} exists")
    models = aip.Model.list(filter=f"displayName={MODEL_DISPLAY_NAME}")

    if len(models) == 0:
        logging.info("No parent model found.")
        parent_model = None
        is_default_version = True
        # version_aliases = ["champion"]
    elif len(models) == 1:
        parent_model = models[0].resource_name
        is_default_version = False
        # version_aliases = ["challenger"]
        logging.info(f"Parent model found: {parent_model}")
    else:
        raise RuntimeError(
            f"Multiple models with name {MODEL_DISPLAY_NAME} were found."
        )

    # Start the training
    uploaded_model = job.run(
        model_display_name=MODEL_DISPLAY_NAME,
        # model_labels=None,
        # model_id: Optional[str] = None,
        parent_model=parent_model,
        is_default_version=is_default_version,
        # model_version_aliases=version_aliases,
        # model_version_description: Optional[str] = None,
        args=CMDARGS,
        replica_count=1,
        machine_type="n1-standard-4",
    )

    logging.info(uploaded_model)
    logging.info(uploaded_model.uri)

    model.metadata[
        "resourceName"
    ] = f"{uploaded_model.resource_name}@{uploaded_model.version_id}"
    model.metadata["containerSpec"] = {"imageUri": DEPLOY_IMAGE}
    model.uri = uploaded_model.uri
    model.TYPE_NAME = "google.VertexModel"

    with open(metrics.path, "r") as fp:
        parsed_metrics = json.load(fp)

    logging.info(parsed_metrics)
    for k, v in parsed_metrics.items():
        if type(v) is float:
            metrics.log_metric(k, v)

    return (parent_model,)


# ARTIFACT_PROPERTY_KEY_RESOURCE_NAME = 'resourceName'
# def google_artifact(type_name):
#   "Decorator for Google Artifact types for handling KFP v1/v2 artifact types"
#   def add_type_name(cls):
#     if hasattr(dsl.Artifact, 'schema_title'):
#       cls.schema_title = type_name
#       cls.schema_version = '0.0.1'
#     else:
#       cls.TYPE_NAME = type_name
#     return cls
#   return add_type_name
#
# @google_artifact('google.VertexModel')
# class VertexModel(dsl.Artifact):
#   """An artifact representing a Vertex Model."""
#
#   def __init__(self, name: str, uri: str, model_resource_name: str):
#     """Args:
#          name: The artifact name.
#          uri: the Vertex Model resource uri, in a form of
#          https://{service-endpoint}/v1/projects/{project}/locations/{location}/models/{model},
#          where
#          {service-endpoint} is one of the supported service endpoints at
#          https://cloud.google.com/vertex-ai/docs/reference/rest#rest_endpoints
#          model_resource_name: The name of the Model resource, in a form of
#          projects/{project}/locations/{location}/models/{model}. For
#          more details, see
#          https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.models/get
#     """
#     super().__init__(
#         uri=uri,
#         name=name,
#         metadata={ARTIFACT_PROPERTY_KEY_RESOURCE_NAME: model_resource_name})
