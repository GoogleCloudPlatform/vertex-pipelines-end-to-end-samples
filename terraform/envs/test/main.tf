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
      # >= 5.10 required for google_workbench_instance (Notebooks v1 is EOL)
      version = "~> 5.40"
    }

    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.40"
    }

  }

  # Terraform state stored in GCS
  backend "gcs" {}
}

locals {
  notebook_instances = length(var.notebook_instances) > 0 ? var.notebook_instances : (
    var.create_notebook ? {
      (var.notebook_name) = { owner = var.notebook_owner }
    } : {}
  )

  notebooks = {
    for name, nb in local.notebook_instances : name => {
      machine_type           = var.notebook_machine_type
      zone                   = var.notebook_zone
      owner                  = nb.owner
      boot_disk_type         = var.notebook_boot_disk_type
      boot_disk_size_gb      = var.notebook_boot_disk_size_gb
      data_disk_type         = var.notebook_data_disk_type
      data_disk_size_gb      = var.notebook_data_disk_size_gb
      no_public_ip           = var.notebook_no_public_ip
      install_gpu_driver     = var.notebook_install_gpu_driver
      accelerator_type       = var.notebook_accelerator_type
      accelerator_core_count = var.notebook_accelerator_core_count
      network                = var.notebook_network
      subnet                 = var.notebook_subnet
      labels                 = {}
    }
  }
}

# Core Vertex Pipelines infrastructure
module "vertex_deployment" {
  source     = "../../modules/vertex_deployment"
  project_id = var.project_id
  region     = var.region
}

# BigQuery dataset for ML data
module "bigquery" {
  source      = "../../modules/bigquery"
  project_id  = var.project_id
  region      = var.region
  dataset_id  = var.dataset_id
  description = "Dataset for ML pipeline data"
  depends_on  = [module.vertex_deployment]
}

# Vertex AI Workbench notebooks
module "notebooks" {
  source     = "../../modules/notebooks"
  project_id = var.project_id
  region     = var.region
  network    = var.notebook_network
  notebooks  = local.notebooks
  depends_on = [module.vertex_deployment]
}
