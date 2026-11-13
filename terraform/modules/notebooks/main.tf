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

locals {
  create_notebooks = length(var.notebooks) > 0
  # Landing-zone VPCs are typically named "<project_id>-vpc" (no "default" network).
  network_name = var.network != "" ? var.network : "${var.project_id}-vpc"
}

## Service Account for notebook VMs ##
resource "google_service_account" "notebooks_sa" {
  project      = var.project_id
  account_id   = "vertex-notebooks"
  display_name = "Vertex Notebooks Service Account"
}

# Newly created service accounts are not immediately visible to IAM.
resource "time_sleep" "wait_for_notebooks_sa" {
  depends_on      = [google_service_account.notebooks_sa]
  create_duration = "30s"
}

## Networking for Workbench (required; empty network fails the API) ##
data "google_compute_network" "notebooks" {
  count   = local.create_notebooks ? 1 : 0
  name    = local.network_name
  project = var.project_id
}

resource "google_compute_subnetwork" "notebooks" {
  count                    = local.create_notebooks ? 1 : 0
  project                  = var.project_id
  name                     = "vertex-notebooks"
  region                   = var.region
  network                  = data.google_compute_network.notebooks[0].id
  ip_cidr_range            = var.subnet_ip_cidr_range
  private_ip_google_access = true
}

# Landing-zone VPCs may omit the default internet route. Private Google Access
# (and Workbench proxy registration) still need 0.0.0.0/0 via the internet gateway.
resource "google_compute_route" "notebooks_default_internet" {
  count            = local.create_notebooks ? 1 : 0
  project          = var.project_id
  name             = "vertex-notebooks-default-internet"
  description      = "Default internet route for Vertex Workbench (PGA / proxy access)"
  dest_range       = "0.0.0.0/0"
  network          = data.google_compute_network.notebooks[0].name
  next_hop_gateway = "default-internet-gateway"
  priority         = 1000
}

## Vertex AI Workbench instances ##
# Notebooks v1 (google_notebooks_instance) is EOL; use Workbench Instances.
resource "google_workbench_instance" "notebooks" {
  for_each = var.notebooks

  project  = var.project_id
  name     = each.key
  location = each.value.zone != "" ? each.value.zone : "${var.region}-a"

  # Empty owner means any user with actAs on the notebook SA can access.
  instance_owners = each.value.owner != "" ? [each.value.owner] : null

  labels = merge(
    {
      managed-by = "terraform"
      component  = "vertex-notebooks"
    },
    each.value.labels,
  )

  gce_setup {
    machine_type      = each.value.machine_type
    disable_public_ip = each.value.no_public_ip

    service_accounts {
      email = google_service_account.notebooks_sa.email
    }

    boot_disk {
      disk_type    = each.value.boot_disk_type
      disk_size_gb = each.value.boot_disk_size_gb
    }

    dynamic "data_disks" {
      for_each = each.value.data_disk_size_gb > 0 ? [1] : []
      content {
        disk_type    = each.value.data_disk_type != "" ? each.value.data_disk_type : "PD_STANDARD"
        disk_size_gb = each.value.data_disk_size_gb
      }
    }

    network_interfaces {
      network = each.value.network != "" ? each.value.network : data.google_compute_network.notebooks[0].id
      subnet  = each.value.subnet != "" ? each.value.subnet : google_compute_subnetwork.notebooks[0].id
    }

    dynamic "accelerator_configs" {
      for_each = each.value.accelerator_type != "" ? [1] : []
      content {
        type       = each.value.accelerator_type
        core_count = each.value.accelerator_core_count
      }
    }

    metadata = {
      terraform = "true"
    }
  }

  timeouts {
    create = "30m"
    update = "30m"
    delete = "30m"
  }

  depends_on = [
    time_sleep.wait_for_notebooks_sa,
    time_sleep.wait_for_notebook_owner_iam,
    google_service_account_iam_member.notebook_owners_can_act_as_sa,
    google_compute_route.notebooks_default_internet,
  ]
}
