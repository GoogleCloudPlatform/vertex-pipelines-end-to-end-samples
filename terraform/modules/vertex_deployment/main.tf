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
  for_each           = toset(var.gcp_service_list)
  project            = var.project_id
  service            = each.key
  disable_on_destroy = var.disable_services_on_destroy
}

## Service Accounts ##

# Vertex Pipelines service account
resource "google_service_account" "pipelines_sa" {
  project      = var.project_id
  account_id   = "vertex-pipelines"
  display_name = "Vertex Pipelines Service Account"
  depends_on   = [google_project_service.gcp_services]
}

# Cloud Function service account
resource "google_service_account" "vertex_cloudfunction_sa" {
  project      = var.project_id
  account_id   = "vertex-cloudfunction-sa"
  display_name = "Cloud Function (Vertex Pipeline trigger) Service Account"
  depends_on   = [google_project_service.gcp_services]
}

## GCS buckets ##
resource "google_storage_bucket" "pipeline_root_bucket" {
  name                        = "${var.project_id}-pl-root"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  depends_on                  = [google_project_service.gcp_services]
}

resource "google_storage_bucket" "pipeline_assets_bucket" {
  name                        = "${var.project_id}-pl-assets"
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  depends_on                  = [google_project_service.gcp_services]
}

## Cloud Function - used to trigger pipelines ##

locals {
  # Cloud Functions not available in all regions
  # Allow the user to override the Cloud Function region using var.cloudfunction_region
  # Otherwise just use var.region
  cloudfunction_region = coalesce(var.cloudfunction_region, var.region)
}

# Pub/Sub topic (for triggering pipelines)
resource "google_pubsub_topic" "pipeline_trigger_topic" {
  name       = var.pubsub_topic_name
  project    = var.project_id
  depends_on = [google_project_service.gcp_services]
}

# Cloud Function staging bucket
resource "google_storage_bucket" "cf_staging_bucket" {
  name                        = "${var.project_id}-cf-staging"
  location                    = local.cloudfunction_region
  project                     = var.project_id
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  depends_on                  = [google_project_service.gcp_services]
}

# Cloud function (for triggering pipelines)
module "cloudfunction" {
  source                        = "../cloudfunction"
  project_id                    = var.project_id
  region                        = local.cloudfunction_region
  function_name                 = var.cloudfunction_name
  description                   = var.cloudfunction_description
  source_dir                    = "../../../pipelines/src/pipelines/trigger"
  source_code_bucket_name       = google_storage_bucket.cf_staging_bucket.name
  runtime                       = "python39"
  entry_point                   = "cf_handler"
  cf_service_account            = google_service_account.vertex_cloudfunction_sa.email
  vpc_connector                 = var.cloudfunction_vpc_connector
  vpc_connector_egress_settings = var.cloudfunction_vpc_connector_egress_settings
  event_trigger = {
    event_type           = "google.pubsub.topic.publish",
    resource             = google_pubsub_topic.pipeline_trigger_topic.id
    retry_policy_enabled = false
  }
  environment_variables = {
    VERTEX_LOCATION      = var.region
    VERTEX_PIPELINE_ROOT = google_storage_bucket.pipeline_root_bucket.url
    VERTEX_PROJECT_ID    = var.project_id
    VERTEX_SA_EMAIL      = google_service_account.pipelines_sa.email
  }
  depends_on = [google_project_service.gcp_services]
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
