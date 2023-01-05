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

variable "project_id" {
  description = "The ID of the project in which to provision resources."
  type        = string
}

variable "api_list" {
  description = "List of Google Cloud APIs to enable on the project."
  type        = list(string)
  default     = []
}

variable "app_engine_region" {
  description = "Region for the App Engine application."
  type        = string
}

variable "vertex_region" {
  description = "Region for Vertex Pipelines execution."
  type        = string
}

variable "service_accounts" {
  description = "Map of service accounts to create."
  type = map(object({
    name          = string
    display_name  = string
    project_roles = list(string)
  }))
  default = {}
}

variable "pubsub_topic_name" {
  description = "Name of the Pub/Sub topic to create for triggering pipelines."
  type        = string
}

variable "gcs_buckets_names" {
  description = "Map of names of GCS buckets to create."
  type        = map(string)
  default     = {}
}

variable "cloud_function_config" {
  description = "Config for the Cloud Function for triggering pipelines."
  type = object({
    name          = string
    region        = string
    description   = string
    vpc_connector = string
  })
}

variable "cloud_schedulers_config" {
  description = "Map of configurations for cloud scheduler jobs (each a different pipeline schedule)."
  type = map(object({
    name                = string
    region              = string
    description         = string
    schedule            = string
    time_zone           = string
    template_path       = string
    enable_caching      = bool
    pipeline_parameters = map(any)
  }))
  default = {}
}
