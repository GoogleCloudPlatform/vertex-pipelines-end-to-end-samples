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

from kfp.dsl import Dataset, Input, Metrics, Model, Output, component
from google_cloud_pipeline_components.types import artifact_types


@component(
    base_image="python:3.9",
    packages_to_install=[
        "google-cloud-aiplatform==1.28.1",
        "google-cloud-pipeline-components==2.1.0",
    ],
)
def upload_model(
    model: Input[Model],
    serving_container_image: str,
    vertex_model: Output[artifact_types.VertexModel],
    project: str,
    location: str,
    model_evaluation: Input[Metrics],
    eval_metric: str,
    eval_lower_is_better: bool,
    model_name: str,
    pipeline_job_id: str,
    test_dataset: Input[Dataset],
    evaluation_name: str = "Imported evaluation",
    order_models_by: str = "create_time desc",
) -> None:
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

    import json
    import logging
    import google.cloud.aiplatform as aip
    from google.protobuf.json_format import MessageToDict

    def lookup_model(
        order_models_by: str,
        location: str,
        project: str,
        model_name: str,
    ) -> aip.Model:

        logging.info(f"listing models with display name {model_name}")
        logging.info(f"choosing model by order ({order_models_by})")
        models = aip.Model.list(
            filter=f'display_name="{model_name}"',
            order_by=order_models_by,
            location=location,
            project=project,
        )
        logging.info(f"found {len(models)} models")

        if len(models) == 0:
            logging.info(
                f"No model found with name {model_name}"
                + f"(project: {project} location: {location})"
            )
            return None
        elif len(models) == 1:
            return models[0]
        else:
            raise RuntimeError(f"Multiple models with name {model_name} were found.")

    def compare_models(
        champion_metrics: dict,
        challenger_metrics: dict,
        eval_metric: str,
        eval_lower_is_better,
    ) -> bool:

        logging.info(f"Comparing {eval_metric} of models")
        logging.debug(f"Champion metrics: {champion_metrics}")
        logging.debug(f"Challenger metrics: {challenger_metrics}")

        m_champ = champion_metrics[eval_metric]
        m_chall = challenger_metrics[eval_metric]
        logging.info(f"Champion={m_champ} Challenger={m_chall}")

        challenger_wins = (
            (m_chall < m_champ) if eval_lower_is_better else (m_chall > m_champ)
        )

        if challenger_wins:
            logging.info("Challenger wins!")
        else:
            logging.info("Champion wins!")

        return challenger_wins

    def import_evaluation(
        parsed_metrics: dict,
        challenger_model: aip.Model,
        location: str,
        evaluation_name: str = "Imported evaluation",
    ):
        from google.cloud.aiplatform_v1 import ModelEvaluation, ModelServiceClient
        from google.protobuf.json_format import ParseDict

        logging.info(f"Parsed metrics: {parsed_metrics}")

        schema_template = (
            "gs://google-cloud-aiplatform/schema/modelevaluation/%s_metrics_1.0.0.yaml"
        )
        schema = schema_template % parsed_metrics.pop("problemType")
        evaluation = {
            "displayName": evaluation_name,
            "metricsSchemaUri": schema,
            "metrics": parsed_metrics,
            "metadata": {
                "pipeline_job_id": pipeline_job_id,
                "evaluation_dataset_type": "gcs",
                "evaluation_dataset_path": [test_dataset.uri],
            },
        }

        request = ParseDict(evaluation, ModelEvaluation()._pb)
        logging.info(f"Request: {request}")

        model_name = challenger_model.versioned_resource_name
        logging.info(model_name)

        client = ModelServiceClient(
            client_options={"api_endpoint": location + "-aiplatform.googleapis.com"}
        )
        response = client.import_model_evaluation(
            parent=model_name,
            model_evaluation=request,
        )
        logging.info(f"Response: {response}")
        return (response.name,)

    # Parse metrics to dict
    with open(model_evaluation.path, "r") as f:
        metrics = json.load(f)

    champion_model = lookup_model(
        order_models_by=order_models_by,
        location=location,
        project=project,
        model_name=model_name,
    )

    if champion_model is not None:
        # Compare models
        logging.info(
            f"Model default version {champion_model.version_id} "
            "is being challenged by new model."
        )
        # Look up Vertex model evaluation for champion model
        eval_champion = champion_model.get_model_evaluation()
        champion_metrics = MessageToDict(eval_champion._gca_resource._pb)["metrics"]

        # Take challenger metrics as input to this component
        challenger_metrics = metrics

        challenger_wins = compare_models(
            champion_metrics=champion_metrics,
            challenger_metrics=challenger_metrics,
            eval_metric=eval_metric,
            eval_lower_is_better=eval_lower_is_better,
        )

    else:
        logging.info("No champion model found, uploading new model.")
        challenger_wins = True

    # Upload model to registry
    uploaded_model = aip.Model.upload(
        display_name=model_name,
        artifact_uri=model.uri,
        serving_container_image_uri=serving_container_image,
        serving_container_predict_route="/predict",
        serving_container_health_route="/healthz",
        parent_model=(
            champion_model.resource_name if champion_model is not None else None
        ),
        is_default_version=challenger_wins,
    )

    # Output google.VertexModel artifact
    vertex_model.uri = (
        f"https://{location}-aiplatform.googleapis.com/v1/"
        f"{uploaded_model.versioned_resource_name}"
    )
    vertex_model.metadata["resourceName"] = uploaded_model.versioned_resource_name

    # Import evaluation to model registry
    import_evaluation(
        location=location,
        parsed_metrics=metrics,
        challenger_model=uploaded_model,
        evaluation_name=evaluation_name,
    )
