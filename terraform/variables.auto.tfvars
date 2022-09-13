/**
 * Copyright 2022 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
api_list = [
  # "storage-api",
  "aiplatform",
  "bigquery",
  # "cloudscheduler",
  # "cloudfunctions",
  # "pubsub",
  # "iam",
  # "appengine",
  # "cloudbuild",
]

app_engine_region = "europe-west4"
bigquery_location = "EU"

pubsub_topic_name = "vertex-pipelines-trigger"

cloud_function_config = {
  name          = "vertex-pipelines-trigger",
  region        = "europe-west4",
  description   = "Vertex Pipeline trigger function",
  vpc_connector = null,
}

cloud_schedulers_config = {
  training = {
    name         = "training-pipeline-trigger",
    region       = "europe-west4",
    description  = "Trigger my training pipeline in Vertex",
    schedule     = "0 0 * * 0",
    time_zone    = "UTC",
    payload_file = "../pipelines/xgboost/training/payloads/dev.json",
  },
}
