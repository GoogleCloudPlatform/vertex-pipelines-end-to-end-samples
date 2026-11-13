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

from kfp.dsl import component, Output, Model
from typing import NamedTuple


@component(
    base_image="python:3.12.8",
    packages_to_install=["google-cloud-aiplatform==1.135.0"],
)
def lookup_model(
    model_name: str,
    location: str,
    project: str,
    model: Output[Model],
    fail_on_model_not_found: bool = False,
) -> NamedTuple(
    "Outputs",
    [
        ("model_resource_name", str),
        ("training_dataset", dict),
        ("training_dataset_gcs_uri", str),
    ],
):
    """
    Fetch a model given a model name (display name) and export to GCS.

    Args:
        model_name (str): display name of the model
        location (str): location of the Google Cloud project
        project (str): project id of the Google Cloud project
        model (Output[Model]): a Vertex AI model
        fail_on_model_not_found (bool): if set to True, raise runtime error if
            model is not found

    Returns:
        model_resource_name (str): Resource name of the found model. Empty string
            if model not found.
        training_dataset (dict): Training dataset metadata for Model Monitoring v1
            (batch prediction skew). Empty dict if unavailable.
        training_dataset_gcs_uri (str): GCS URI (CSV) of the training data used as
            a Model Monitoring v2 baseline for online/endpoint monitoring.
            Empty string if unavailable.
    """

    import json
    import logging
    import os
    from pathlib import Path
    from google.cloud.aiplatform import Model

    TRAINING_DATASET_INFO = "training_dataset.json"

    logging.info(f"listing models with display name {model_name}")
    models = Model.list(
        filter=f'display_name="{model_name}"',
        location=location,
        project=project,
    )
    logging.info(f"found {len(models)} model(s)")

    training_dataset = {}
    training_dataset_gcs_uri = ""
    model_resource_name = ""
    if len(models) == 0:
        logging.error(
            f"No model found with name {model_name} "
            + f"(project: {project} location: {location})"
        )
        if fail_on_model_not_found:
            raise RuntimeError(f"Failed as model was not found")
    elif len(models) == 1:
        target_model = models[0]
        model_resource_name = target_model.resource_name
        # Model.list() returns the default version, but resource_name is often
        # unversioned. Stamp @version_id so deploy and Model Monitoring v2
        # target the same champion version (Vertex allows one monitor per
        # version; an unversioned name would be treated as version 1).
        version_id = getattr(target_model, "version_id", None)
        if isinstance(version_id, str) and version_id:
            if "@" not in model_resource_name:
                model_resource_name = f"{model_resource_name}@{version_id}"
            model.metadata["versionId"] = version_id
        logging.info(f"model display name: {target_model.display_name}")
        logging.info(f"model resource name: {model_resource_name}")
        logging.info(f"model uri: {target_model.uri}")
        model.uri = target_model.uri
        model.metadata["resourceName"] = model_resource_name

        path = Path(model.path) / TRAINING_DATASET_INFO
        logging.info(f"Reading training dataset metadata: {path}")

        if os.path.exists(path):
            with open(path, "r") as fp:
                training_dataset = json.load(fp)
            uris = training_dataset.get("gcsSource", {}).get("uris", [])
            if uris:
                training_dataset_gcs_uri = uris[0]
                # Older training runs stored the local Cloud Storage FUSE mount
                # path (e.g. "/gcs/bucket/object") instead of a "gs://" URI.
                # Model Monitoring v1 and v2 both require a proper "gs://" URI.
                if training_dataset_gcs_uri.startswith("/gcs/"):
                    training_dataset_gcs_uri = (
                        "gs://" + training_dataset_gcs_uri[len("/gcs/") :]
                    )
                    training_dataset.setdefault("gcsSource", {})["uris"] = [
                        training_dataset_gcs_uri
                    ]
        else:
            logging.warning("Training dataset metadata doesn't exist!")
    else:
        raise RuntimeError(f"Multiple models with name {model_name} were found.")

    return model_resource_name, training_dataset, training_dataset_gcs_uri
