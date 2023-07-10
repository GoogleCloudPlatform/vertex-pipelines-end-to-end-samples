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

from kfp.dsl import Input, Model, component


@component(
    base_image="python:3.7",
    packages_to_install=["google-cloud-aiplatform==1.24.1"],
)
def update_best_model(
    challenger: Input[Model],
    challenger_evaluation: str,
    parent_model: str,
    project_id: str,
    project_location: str,
    eval_metric: str,
    eval_lower_is_better: bool,
    model_alias: str = "default",
) -> NamedTuple("Outputs", [("challenger_wins", bool)]):
    """
    Args:
        challenger (Model): Challenger model.
        challenger_evaluation (str): Resource URI of challenger model evaluation e.g.
            `projects/.../locations/.../models/.../evaluations/...`
        parent_model (str): Resource URI of parent model.
        eval_metric (str): Metric to compare champion and challenger on.
        eval_lower_is_better (bool): Usually True for losses and
            False for classification metrics.
        project_id (str): project id of the Google Cloud project.
        project_location (str): location of the Google Cloud project.
        model_alias (str): alias of the parent model.
    """

    import logging
    import google.cloud.aiplatform as aip
    from google.cloud.aiplatform.models import ModelRegistry
    from google.protobuf.json_format import MessageToDict

    logging.info("Get models...")
    if model_alias:
        parent_model += "@" + model_alias
    champion = aip.Model(parent_model)
    challenger = aip.Model(challenger.metadata["resourceName"])
    logging.info(
        f"Model default version {champion.version_id} "
        f"is being challenged by version {challenger.version_id}!"
    )

    eval_champion = challenger.get_model_evaluation()
    eval_challenger = aip.model_evaluation.ModelEvaluation(challenger_evaluation)
    metrics_champion = MessageToDict(eval_champion._gca_resource._pb)["metrics"]
    metrics_challenger = MessageToDict(eval_challenger._gca_resource._pb)["metrics"]

    logging.info(f"Comparing {eval_metric} of models")
    logging.debug(f"Champion metrics: {metrics_champion}")
    logging.debug(f"Challenger metrics: {metrics_challenger}")

    m_champ = metrics_champion[eval_metric]
    m_chall = metrics_challenger[eval_metric]
    logging.info(f"Champion={m_champ} Challenger={m_chall}")

    challenger_wins = (
        (m_chall < m_champ) if eval_lower_is_better else (m_chall > m_champ)
    )
    if challenger_wins:
        logging.info(f"Updating champion to version: {challenger.version_id}")
        model_registry = ModelRegistry(
            model=champion, project=project_id, location=project_location
        )
        model_registry.add_version_aliases(["default"], challenger.version_id)
        return (True,)

    logging.info(f"Keeping current champion!")
    return (False,)
