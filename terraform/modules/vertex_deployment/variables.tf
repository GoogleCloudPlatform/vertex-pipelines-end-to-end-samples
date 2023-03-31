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
  description = "The ID of the Google Cloud project in which to provision resources."
  type        = string
}

variable "region" {
  description = "Google Cloud region to use for resources and Vertex Pipelines execution."
  type        = string
}

variable "gcp_service_list" {
  description = "List of Google Cloud APIs to enable on the project."
  type        = list(string)
  default = [
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "bigquerydatatransfer.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "dataflow.googleapis.com",
    "iam.googleapis.com",
    "monitoring.googleapis.com",
    "pubsub.googleapis.com",
    "secretmanager.googleapis.com",
    "storage-api.googleapis.com",
    "storage-component.googleapis.com",
    "storage.googleapis.com",
  ]
}

variable "disable_services_on_destroy" {
  description = "If true, disable the service when the Terraform resource is destroyed. Defaults to true. May be useful in the event that a project is long-lived but the infrastructure running in that project changes frequently."
  type        = bool
  default     = true
}

variable "cloudfunction_region" {
  description = "Google Cloud region to use for the Cloud Function (and CF staging bucket). Defaults to the same as var.region"
  type        = string
  default     = null
}

variable "pubsub_topic_name" {
  description = "Name of the Pub/Sub topic to create for triggering pipelines."
  type        = string
  default     = "vertex-pipeline-trigger"
}

variable "cloudfunction_name" {
  description = "Name of the Cloud Function"
  type        = string
  default     = "vertex-pipelines-trigger"
}

variable "cloudfunction_description" {
  description = "Description for the Cloud Function"
  type        = string
  default     = "Cloud Function used to trigger Vertex Pipelines"
}

variable "cloudfunction_vpc_connector" {
  description = "The VPC Network Connector that the cloud function can connect to. It should be set up as fully-qualified URI. The format of this field is projects/*/locations/*/connectors/*"
  type        = string
  default     = null
}

variable "cloudfunction_vpc_connector_egress_settings" {
  description = "The egress settings for the connector, controlling what traffic is diverted through it. Allowed values are ALL_TRAFFIC and PRIVATE_RANGES_ONLY. Defaults to PRIVATE_RANGES_ONLY. If unset, this field preserves the previously set value."
  type        = string
  default     = null
}

variable "cloud_schedulers_config" {
  description = "Map of configurations for cloud scheduler jobs (each a different pipeline schedule)."
  type = map(object({
    name                = string
    description         = string
    schedule            = string
    time_zone           = string
    template_path       = string
    enable_caching      = bool
    pipeline_parameters = map(any)
  }))
  default = {}
}

variable "pipelines_sa_project_roles" {
  description = "List of project IAM roles to be granted to the Vertex Pipelines service account."
  type        = list(string)
  default = [
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
  ]
}

variable "cloudfunction_sa_project_roles" {
  description = "List of project IAM roles to be granted to the Cloud Function service account."
  type        = list(string)
  default = [
    "roles/aiplatform.user",
    "roles/logging.logWriter",
  ]
}
