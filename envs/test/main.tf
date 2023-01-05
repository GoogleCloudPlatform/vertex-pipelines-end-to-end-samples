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


terraform {
  required_version = ">= 0.13"
  required_providers {

    google = {
      source  = "hashicorp/google"
      version = "~> 4.9.0"
    }
  }

  # Terraform state stored in GCS
  backend "gcs" {
    bucket = "my-tfstate-bucket" # Change this
    prefix = "/path/to/tfstate"  # Change this
  }
}


# Cloud Scheduler jobs (for triggering pipelines)
module "scheduler" {
  for_each       = var.cloud_schedulers_config
  source         = "./modules/pubsub_scheduler"
  project_id     = var.project_id
  region         = each.value.region
  scheduler_name = each.value.name
  description    = lookup(each.value, "description", null)
  schedule       = each.value.schedule
  time_zone      = lookup(each.value, "time_zone", "UTC")
  topic_id       = module.pubsub.id
  attributes = {
    template_path  = each.value.template_path,
    enable_caching = lookup(each.value, "enable_caching", null)
  }
  data = base64encode(jsonencode(each.value.pipeline_parameters))
}
