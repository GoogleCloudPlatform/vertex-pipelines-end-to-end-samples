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

# BigQuery Components

A python package which provides common BigQuery components for interacting with BigQuery.
Currently, the following components are implemented:

- `bq_query_to_table`: Execute a SQL query and persist results in a table.
- `extract_bq_to_dataset`: Export a table to a KubeFlow dataset on Cloud Storage.

These components either augment, extend, or add new functionalities that aren't found in [Google Cloud Pipeline Components list](https://cloud.google.com/vertex-ai/docs/pipelines/gcpc-list).
