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

## Google Cloud APIs to enable ##
resource "google_project_service" "gcp_services" {
  for_each                   = toset(var.gcp_service_list)
  project                    = var.project_id
  service                    = each.key
  disable_on_destroy         = var.disable_services_on_destroy
  disable_dependent_services = var.disable_dependent_services
}

## Service Accounts ##

# Vertex Pipelines service account
resource "google_service_account" "pipelines_sa" {
  project      = var.project_id
  account_id   = "vertex-pipelines"
  display_name = "Vertex Pipelines Service Account"
  depends_on   = [google_project_service.gcp_services]
}

# Allow time for the service account to be created and propagated before granting it IAM roles.
# Newly created service accounts are not immediately visible to IAM, which
# causes "Service account ... does not exist" errors on apply.
resource "time_sleep" "wait_for_pipelines_sa" {
  depends_on      = [google_service_account.pipelines_sa]
  create_duration = "30s"
}

## GCS buckets ##
resource "google_storage_bucket" "pipeline_root_bucket" {
  name                        = "${var.project_id}-pl-root"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true
  depends_on                  = [google_project_service.gcp_services]
}

# Cloud Build staging bucket is created by the landing zone; look it up for IAM/outputs.
data "google_storage_bucket" "staging_bucket" {
  name = "${var.project_id}-staging"
}

## Vertex Metadata store ##
resource "google_vertex_ai_metadata_store" "default_metadata_store" {
  provider    = google-beta
  name        = "default"
  description = "Default metadata store"
  project     = var.project_id
  region      = var.region
  depends_on  = [google_project_service.gcp_services]
}

## Artifact Registry - container images ##
resource "google_artifact_registry_repository" "vertex-images" {
  repository_id = "vertex-images"
  description   = "Container image repository for training container images"
  project       = var.project_id
  location      = var.region
  format        = "DOCKER"
  depends_on    = [google_project_service.gcp_services]
}

## Artifact Registry - KFP pipelines ##
resource "google_artifact_registry_repository" "vertex-pipelines" {
  repository_id = "vertex-pipelines"
  description   = "KFP repository for Vertex Pipelines"
  project       = var.project_id
  location      = var.region
  format        = "KFP"
  depends_on    = [google_project_service.gcp_services]
}
