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

A Python package which provides common KubeFlow components for interacting with Vertex AI.
Currently, the following components are implemented:

- `upload_model`: Uploads a new model version to the Vertex Model Registry, importing a model evaluation, and updating the "default" tag on the model if the new version (challenger) is superior to the previous (champion) model.
- `model_batch_predict`: Run a [Batch Prediction Job](https://cloud.google.com/ai-platform/prediction/docs/batch-predict).

These components either augment, extend, or add new functionalities that aren't found in [Google Cloud Pipeline Components list](https://cloud.google.com/vertex-ai/docs/pipelines/gcpc-list).
