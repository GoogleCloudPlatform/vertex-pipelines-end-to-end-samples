<!-- 
Copyright 2023 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
 -->
# Kubeflow Pipelines Components

The package `components` contains KubeFlow pipeline components for interacting with Google Cloud.
The following components are implemented:

- `extract_table`: Extract a table from BigQuery to Cloud Storage.
- `lookup_model`: Look up a mode in the Vertex AI Model Registry given a name (and version optionally).
- `model_batch_predict`: Run a [Batch Prediction Job](https://cloud.google.com/ai-platform/prediction/docs/batch-predict).
- `upload_model`: Uploads a new model version to the Vertex Model Registry, importing a model evaluation, and updating the "default" tag on the model if the new version (challenger) is superior to the previous (champion) model.

These components either augment, extend, or add new functionalities that aren't found in [Google Cloud Pipeline Components list](https://cloud.google.com/vertex-ai/docs/pipelines/gcpc-list).

## Creating a new pipeline components package

Update Python dependencies in `poetry.lock`, `pyproject.toml`, and in `packages_to_install` (in the `@component` decorator):

- In `pyproject.toml`, add any dependencies that your component uses under `[tool.poetry.dependencies]`(each pinned to a specific version)
- In `packages_to_install` (in the `@component` decorator used to define your component), add any dependencies that your component uses (each pinned to a specific version)

Define your pipeline components using the `@component` decorator in Python files under `components/src/components`. 
You will need to update the `__init__.py` file to provide tests.
See the [Kubeflow Pipelines documentation](https://www.kubeflow.org/docs/components/pipelines/v1/sdk-v2/python-function-components/#building-python-function-based-components) for more information about writing pipeline components.

Finally, you will need to install this new components package into the [`pipelines`](../pipelines) package.
Run `make install` from the root of the repository to install the new components.

## Testing components

Unit tests for components are defined using pytest and should be created under `components/tests`. 
Take a look at the existing components to see examples of how you can write these tests and perform mocking/patching of KFP Artifact types.

To run the unit tests, run `make test` from the root of the repository. 

