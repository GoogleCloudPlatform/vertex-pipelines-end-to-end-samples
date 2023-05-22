<!-- 
Copyright 2022 Google LLC

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

# Vertex Components

A python package which provides common KubeFlow components for interacting with Vertex AI.
Currently, the following components are implemented:

- `custom_train_job`: Train a model in a [Custom Training Job](https://cloud.google.com/vertex-ai/docs/training/create-custom-job).
- `import_model_evaluation`: Import model evaluation results to a model in the model registry.
- `lookup_model`: Look up a model which was previously uploaded to the model registry.
- `model_batch_predict`: Run a [Batch Prediction Job](https://cloud.google.com/ai-platform/prediction/docs/batch-predict).
- `update_best_model`: Using two model evaluations and a comparison metric, update the better model to the default model.

These components either augment, extend, or add new functionalities that aren't found in [Google Cloud Pipeline Components list](https://cloud.google.com/vertex-ai/docs/pipelines/gcpc-list).
