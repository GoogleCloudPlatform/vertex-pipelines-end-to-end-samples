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
# Trigger pipeline runs

The simplest way to trigger a pipeline run in the sandbox environment is to use the following make command:
```
make run pipeline=<training|prediction>
```
This command compiles the pipeline, copies assets to GCS, and then triggers the pipeline.

### `make run` requires the following environment variables:
When you run the pipeline using the Make command, the pipeline is run from a payload `.json`. This command relies on several `.env.sh` variables which you must specify beforehand. These variables are:
- `VERTEX_PROJECT_ID`: your project id
- `VERTEX_LOCATION`: your project location
- `VERTEX_PIPELINE_ROOT`: URI for root directory
- `VERTEX_SA_EMAIL`: service account
- `VERTEX_CMEK_IDENTIFIER`: customer-managed encryption key (can be `""` or `None`)
- `VERTEX_NETWORK`: private network (can be `""` or `None`)
- `PIPELINE_TEMPLATE`: the pipeline template you want to use
- `PAYLOAD`: name of your payload file under `pipelines/<PIPELINE_TEMPLATE>/<training|prediction>/payloads/` (e.g. `dev.json`)

**NB**: Please note that the Cloud Function service account will need permission to:
- read from the bucket where the compiled pipeline is stored
- have "service account user" permission on the service account being used to run the Vertex pipelines
- subscribe to the pub/sub topic)

## Testing the trigger
To run the unit tests developed for the trigger code, use the following make command:
```
make trigger-tests
```
