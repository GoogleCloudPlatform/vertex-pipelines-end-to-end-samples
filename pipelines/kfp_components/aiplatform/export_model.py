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

from kfp.v2.dsl import Output, Model, component
from pipelines.kfp_components.dependencies import PYTHON37, GOOGLE_CLOUD_AIPLATFORM


@component(base_image=PYTHON37, packages_to_install=[GOOGLE_CLOUD_AIPLATFORM])
def export_model(
    model_resource_name: str,
    model: Output[Model],
    project_location: str = None,
    project_id: str = None,
) -> None:
    """
    Fetch a model given a model name (display name) and export to GCS.

    Args:
        model_resource_name (str): Resource name of the model to export
        model (Output[Model]): output model to be exported to GCS
        project_location (str): location of the Google Cloud project. Defaults to None.
        project_id (str): project id of the Google Cloud project. Defaults to None.
    Returns:
        None
    """

    import logging
    from google.cloud.aiplatform import Model

    model_to_be_exported = Model(model_resource_name)
    logging.info(f"model display name: {model_to_be_exported.display_name}")
    logging.info(f"model resource name: {model_to_be_exported.resource_name}")
    logging.info(f"model uri: {model_to_be_exported.uri}")

    logging.info(f"export model to {model.uri}")
    result = model_to_be_exported.export_model(
        export_format_id="custom-trained",
        artifact_destination=model.uri,
        sync=True,
    )

    # artifactOutputUri could include a separate sub-folder containing the
    # model, so update the model path to include it
    model.path = result["artifactOutputUri"]
    model.metadata["resourceName"] = model_resource_name
    model.metadata["model_labels"] = model_to_be_exported.labels["model_label"]
    logging.info(f"exported model to {model.path}")
