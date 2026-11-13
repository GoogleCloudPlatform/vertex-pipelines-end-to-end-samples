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

variable "region" {
  description = "Google Cloud region to use for resources and Vertex Pipelines execution."
  type        = string
}

variable "dataset_id" {
  description = "The BigQuery dataset ID."
  type        = string
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

# --- Notebook settings (override via notebooks.auto.tfvars) ---

variable "create_notebook" {
  description = "If true and notebook_instances is empty, create a single notebook from notebook_name/notebook_owner."
  type        = bool
  default     = false
}

variable "notebook_instances" {
  description = <<-EOT
    Map of Workbench instances to create. Keys are instance names; each value needs an owner email.
    Preferred way to create one or many notebooks (e.g. hackathon participants).
  EOT
  type = map(object({
    owner = string
  }))
  default = {}
}

variable "notebook_name" {
  description = "Name of the notebook instance when using the single-notebook fallback (notebook_instances empty)."
  type        = string
  default     = "vertex-workbench"
}

variable "notebook_owner" {
  description = "Owner email for the single-notebook fallback. Prefer notebook_instances for multiple people."
  type        = string
  default     = ""
}

variable "notebook_machine_type" {
  description = "Compute Engine machine type for the notebook VM."
  type        = string
  default     = "e2-standard-4"
}

variable "notebook_zone" {
  description = "Zone for the notebook VM. Empty uses \"<region>-a\"."
  type        = string
  default     = ""
}

variable "notebook_boot_disk_type" {
  description = "Boot disk type (e.g. PD_SSD, PD_STANDARD, PD_BALANCED)."
  type        = string
  default     = "PD_SSD"
}

variable "notebook_boot_disk_size_gb" {
  description = "Boot disk size in GB (Workbench images require at least 150)."
  type        = number
  default     = 150
}

variable "notebook_data_disk_type" {
  description = "Optional data disk type. Empty skips attaching a data disk."
  type        = string
  default     = ""
}

variable "notebook_data_disk_size_gb" {
  description = "Optional data disk size in GB. 0 skips attaching a data disk."
  type        = number
  default     = 0
}

variable "notebook_no_public_ip" {
  description = "If true, do not assign a public IP to the notebook."
  type        = bool
  default     = true
}

variable "notebook_network" {
  description = "Optional VPC network short name. Empty defaults to \"<project_id>-vpc\" (landing zone). Per-notebook override still uses notebook map fields."
  type        = string
  default     = ""
}

variable "notebook_subnet" {
  description = "Optional subnet self-link. Empty creates/uses the module vertex-notebooks subnet."
  type        = string
  default     = ""
}

variable "notebook_install_gpu_driver" {
  description = "If true, install a GPU driver (requires accelerator_type)."
  type        = bool
  default     = false
}

variable "notebook_accelerator_type" {
  description = "Optional accelerator type (e.g. NVIDIA_TESLA_T4). Empty for CPU-only."
  type        = string
  default     = ""
}

variable "notebook_accelerator_core_count" {
  description = "Number of accelerator cores when accelerator_type is set."
  type        = number
  default     = 0
}
