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


@component(
    base_image="python:3.7",
    packages_to_install=["google-cloud-aiplatform>=1.24.1"],
    output_component_file=str(Path(__file__).with_suffix(".yaml")),
)
def update_model(
    challenger: Input[Model],
    challenger_evaluation: str,
    parent_model: str,
    primary_metric: str,
    project_id: str,
    project_location: str,
):
    """
    Fetch a model given a model name (display name) and export to GCS.

    Args:
        display_name (str): Required. The display name of the Model. The name can
        be up to 128 characters long and can be consist of any UTF-8 characters.
    """

    import logging
    import google.cloud.aiplatform as aip
    from google.cloud.aiplatform.models import ModelRegistry
    from google.protobuf.json_format import MessageToDict

    logging.info("Get models...")
    champion = aip.Model(f"{parent_model}@default")
    challenger = aip.Model(challenger.metadata["resourceName"])
    logging.info(
        f"Model default version {champion.version_id} "
        f"is being challenged by version {challenger.version_id}!"
    )

    eval_champion = challenger.get_model_evaluation()
    eval_challenger = aip.model_evaluation.ModelEvaluation(challenger_evaluation)
    metrics_champion = MessageToDict(eval_champion._gca_resource._pb)["metrics"]
    metrics_challenger = MessageToDict(eval_challenger._gca_resource._pb)["metrics"]
    metrics_challenger[primary_metric] -= 0.001  # TODO fake

    logging.info(f"Comparing {primary_metric} of models")
    logging.debug(f"Champion metrics: {metrics_champion}")
    logging.debug(f"Challenger metrics: {metrics_challenger}")

    # TODO if eval with same test dataset doesn't exist for both models, what to do?
    logging.info(
        f"Champion={metrics_champion[primary_metric]} "
        f"Challenger={metrics_challenger[primary_metric]}"
    )
    if metrics_champion[primary_metric] > metrics_challenger[primary_metric]:
        logging.info(f"Updating champion to version: {challenger.version_id}")
        model_registry = ModelRegistry(
            model=champion, project=project_id, location=project_location
        )
        model_registry.add_version_aliases(["default"], challenger.version_id)
    else:
        logging.info(f"Keeping current champion!")
