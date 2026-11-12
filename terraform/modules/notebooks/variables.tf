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
  description = "The ID of the Google Cloud project in which to provision notebook instances."
  type        = string
}

variable "region" {
  description = "Google Cloud region used to derive the default zone (<region>-a) when a notebook does not set zone."
  type        = string
}

variable "notebooks" {
  description = <<-EOT
    Map of Vertex AI Workbench instances to create.
    Keys are used as the notebook instance names.
    Leave empty to skip creating notebooks.
  EOT
  type = map(object({
    machine_type           = string
    zone                   = string
    owner                  = string
    boot_disk_type         = string
    boot_disk_size_gb      = number
    data_disk_type         = string
    data_disk_size_gb      = number
    no_public_ip           = bool
    install_gpu_driver     = bool
    accelerator_type       = string
    accelerator_core_count = number
    network                = string
    subnet                 = string
    labels                 = map(string)
  }))
  default = {}
}

variable "network" {
  description = <<-EOT
    VPC network name (short name, not self-link) used when a notebook does not set network.
    Defaults to "<project_id>-vpc" to match typical landing-zone naming.
  EOT
  type        = string
  default     = ""
}

variable "subnet_ip_cidr_range" {
  description = "CIDR for the vertex-notebooks subnet created when notebooks are provisioned."
  type        = string
  default     = "10.250.0.0/24"
}

variable "notebooks_sa_project_roles" {
  description = "List of project IAM roles granted to the Vertex Notebooks service account."
  type        = list(string)
  default = [
    "roles/aiplatform.user",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/storage.objectAdmin",
    "roles/artifactregistry.reader",
    "roles/logging.logWriter",
  ]
}
