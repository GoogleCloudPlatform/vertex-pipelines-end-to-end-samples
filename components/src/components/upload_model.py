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
from google_cloud_pipeline_components.types.artifact_types import VertexModel


@component(
    base_image="python:3.9",
    packages_to_install=[
        "google-cloud-aiplatform==1.30.1",
        "google-cloud-pipeline-components==2.1.0",
    ],
)
def upload_model(
    model: Input[Model],
    test_data: Input[Dataset],
    model_evaluation: Input[Metrics],
    vertex_model: Output[VertexModel],
    project: str,
    location: str,
    model_name: str,
    eval_metric: str,
    eval_lower_is_better: bool,
    pipeline_job_id: str,
    serving_container_image: str,
    model_description: str = None,
    evaluation_name: str = "Imported evaluation",
) -> None:
    """
    Args:
        model (Model): Input challenger model.
        test_data (Dataset): Test dataset used for evaluating challenger model.
        vertex_model (VertexModel): Output model uploaded to Vertex AI Model Registry.
        model_evaluation (Metrics): Evaluation metrics of challenger model.
        project (str): project id of the Google Cloud project.
        location (str): location of the Google Cloud project.
        pipeline_job_id (str):
        model_name (str): Name of champion and challenger model in
            Vertex AI Model Registry.
        eval_metric (str): Metric name to compare champion and challenger on.
        eval_lower_is_better (bool): Usually True for losses and
            False for classification metrics.
        serving_container_image (str): Container URI for serving the challenger
            model.
        model_description (str): Optional. Description of model.
        evaluation_name (str): Optional. Name of evaluation results which are
            displayed in the Vertex AI UI of the challenger model.
    """

    import json
    import logging
    import google.cloud.aiplatform as aip
    from google.protobuf.json_format import MessageToDict
    from google.cloud.aiplatform_v1 import ModelEvaluation, ModelServiceClient
    from google.protobuf.json_format import ParseDict

    def lookup_model(model_name: str) -> aip.Model:
        """Look up model in model registry."""
        logging.info(f"listing models with display name {model_name}")
        models = aip.Model.list(
            filter=f'display_name="{model_name}"',
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
        eval_lower_is_better: bool,
    ) -> bool:
        """Compare models by evaluating a primary metric."""
        logging.info(f"Comparing {eval_metric} of models")
        logging.debug(f"Champion metrics: {champion_metrics}")
        logging.debug(f"Challenger metrics: {challenger_metrics}")

        m_champ = champion_metrics[eval_metric]
        m_chall = challenger_metrics[eval_metric]
        logging.info(f"Champion={m_champ} Challenger={m_chall}")

        challenger_wins = (
            (m_chall < m_champ) if eval_lower_is_better else (m_chall > m_champ)
        )
        logging.info(f"{'Challenger' if challenger_wins else 'Champion'} wins!")

        return challenger_wins

    def upload_model_to_registry(
        is_default_version: bool, parent_model_uri: str = None
    ) -> Model:
        """Upload model to registry."""
        logging.info(f"Uploading model {model_name} (default: {is_default_version}")
        uploaded_model = aip.Model.upload(
            display_name=model_name,
            description=model_description,
            artifact_uri=model.uri,
            serving_container_image_uri=serving_container_image,
            serving_container_predict_route="/predict",
            serving_container_health_route="/health",
            parent_model=parent_model_uri,
            is_default_version=is_default_version,
        )
        logging.info(f"Uploaded model {uploaded_model}")

        # Output google.VertexModel artifact
        vertex_model.uri = (
            f"https://{location}-aiplatform.googleapis.com/v1/"
            f"{uploaded_model.versioned_resource_name}"
        )
        vertex_model.metadata["resourceName"] = uploaded_model.versioned_resource_name

        return uploaded_model

    def import_evaluation(
        parsed_metrics: dict,
        challenger_model: aip.Model,
        evaluation_name: str,
    ) -> str:
        """Import model evaluation."""
        logging.info(f"Evaluation metrics: {parsed_metrics}")
        problem_type = parsed_metrics.pop("problemType")
        schema = (
            f"gs://google-cloud-aiplatform/schema/modelevaluation/"
            f"{problem_type}_metrics_1.0.0.yaml"
        )
        evaluation = {
            "displayName": evaluation_name,
            "metricsSchemaUri": schema,
            "metrics": parsed_metrics,
            "metadata": {
                "pipeline_job_id": pipeline_job_id,
                "evaluation_dataset_type": "gcs",
                "evaluation_dataset_path": [test_data.uri],
            },
        }

        request = ParseDict(evaluation, ModelEvaluation()._pb)
        logging.debug(f"Request: {request}")
        challenger_name = challenger_model.versioned_resource_name
        client = ModelServiceClient(
            client_options={"api_endpoint": location + "-aiplatform.googleapis.com"}
        )
        logging.info(f"Uploading model evaluation for {challenger_name}")
        response = client.import_model_evaluation(
            parent=challenger_name,
            model_evaluation=request,
        )
        logging.debug(f"Response: {response}")
        return response.name

    # Parse metrics to dict
    with open(model_evaluation.path, "r") as f:
        challenger_metrics = json.load(f)

    champion_model = lookup_model(model_name=model_name)

    challenger_wins = True
    parent_model_uri = None
    if champion_model is None:
        logging.info("No champion model found, uploading new model.")
    else:
        # Compare models
        logging.info(
            f"Model default version {champion_model.version_id} "
            "is being challenged by new model."
        )
        # Look up Vertex model evaluation for champion model
        champion_eval = champion_model.get_model_evaluation()
        champion_metrics = MessageToDict(champion_eval._gca_resource._pb)["metrics"]

        challenger_wins = compare_models(
            champion_metrics=champion_metrics,
            challenger_metrics=challenger_metrics,
            eval_lower_is_better=eval_lower_is_better,
        )
        parent_model_uri = champion_model.resource_name

    model = upload_model_to_registry(challenger_wins, parent_model_uri)
    import_evaluation(
        parsed_metrics=challenger_metrics,
        challenger_model=model,
        evaluation_name=evaluation_name,
    )
