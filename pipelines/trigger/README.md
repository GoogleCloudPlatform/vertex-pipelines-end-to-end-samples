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
# Trigger pipeline runs in the sandbox environment

The simplest way to trigger a pipeline run in the sandbox environment is to use the following make command:
```
make run pipeline=<training|prediction> [ enable_caching=<true|false> ]
```
This command compiles the pipeline, copies assets to GCS, and then triggers the pipeline. It relies on several environment variables which you must specify beforehand in `env.sh`. These variables are:

- `VERTEX_PROJECT_ID`: your project id
- `VERTEX_LOCATION`: your project location
- `VERTEX_PIPELINE_ROOT`: URI for root directory
- `VERTEX_SA_EMAIL`: service account
- `VERTEX_CMEK_IDENTIFIER`: customer-managed encryption key (can be `""` or `None`)
- `VERTEX_NETWORK`: private network (can be `""` or `None`)

### Deploy as a Cloud Function

This directory can also be deployed as a Cloud Function to trigger pipeline runs from a Pub/Sub message. The format of the Pub/Sub message is as follows:

#### Pub/Sub attributes

- `template_path` - the GCS path to the compiled KFP pipeline definition (JSON)
- `enable_caching` (optional) - True or False. This can be used to override the default Vertex Pipelines caching behaviour.

#### Pub/Sub data

The data field contains the pipeline input parameters as a JSON string, encoded using base64 encoding.

**NB**: Please note that the Cloud Function service account will need permission to:
- read from the bucket where the compiled pipeline is stored
- have "service account user" permission on the service account being used to run the Vertex pipelines
- subscribe to the pub/sub topic)

## Testing the trigger
To run the unit tests developed for the trigger code, use the following make command:
```
make trigger-tests
```
