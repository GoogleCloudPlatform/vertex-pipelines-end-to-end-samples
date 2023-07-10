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

from kfp.dsl import Input, Model, Metrics, component, Dataset
from typing import NamedTuple


@component(
    base_image="python:3.7",
    packages_to_install=[
        "google-cloud-aiplatform==1.24.1",
    ],
)
def import_model_evaluation(
    model: Input[Model],
    metrics: Input[Metrics],
    test_dataset: Input[Dataset],
    pipeline_job_id: str,
    project_location: str,
    evaluation_name: str = "Imported evaluation",
) -> NamedTuple("Outputs", [("model_evaluation", str)]):
    """Import an evaluation result for a model version.

    Args:
        model (Model): Input model version.
        metrics (Metrics): Input metrics. The contents of the artifact are expected
            to follow the evaluation schema linked in the docs:
            https://cloud.google.com/vertex-ai/docs/evaluation/introduction#features.
        test_dataset (Dataset): Input test dataset which will be linked to evaluation.
        pipeline_job_id (str): Pipeline job id which will be linked to evaluation.
        project_location (str): Location of the Google Cloud project.
        evaluation_name (str): Display name of model evaluation.
    Returns:
        model_evaluation (str): Resource URI of imported model evaluation.
    """
    import json
    import logging
    from google.cloud.aiplatform_v1 import ModelEvaluation, ModelServiceClient
    from google.protobuf.json_format import ParseDict

    logging.info(f"Read metrics from: {metrics.path}")
    with open(metrics.path) as fp:
        parsed_metrics = json.load(fp)
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

    model_name = model.metadata["resourceName"]
    logging.info(model_name)

    client = ModelServiceClient(
        client_options={"api_endpoint": project_location + "-aiplatform.googleapis.com"}
    )
    response = client.import_model_evaluation(
        parent=model_name,
        model_evaluation=request,
    )
    logging.info(f"Response: {response}")
    return (response.name,)
