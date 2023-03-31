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

## Cloud Scheduler jobs (for triggering pipelines) ##
resource "google_cloud_scheduler_job" "scheduled_pipeline" {
  name        = var.name
  project     = var.project_id
  region      = var.region
  description = var.description
  schedule    = var.schedule
  time_zone   = var.time_zone

  pubsub_target {
    topic_name = var.topic_name
    attributes = {
      template_path  = var.template_path,
      enable_caching = var.enable_caching
    }
    data = base64encode(jsonencode(var.pipeline_parameters))
  }
}
