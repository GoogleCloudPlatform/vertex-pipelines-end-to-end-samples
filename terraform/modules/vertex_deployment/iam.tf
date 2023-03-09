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

# Give pipelines SA access to objects
# in the pipeline_root bucket
resource "google_storage_bucket_iam_member" "pipelines_sa_pipeline_root_bucket_iam" {
  for_each = toset([
    "roles/storage.objectAdmin",
    "roles/storage.legacyBucketReader",
  ])
  bucket = google_storage_bucket.pipeline_root_bucket.name
  member = google_service_account.pipelines_sa.member
  role   = each.key
}

# Give pipelines SA read-only access to objects in "assets" bucket
resource "google_storage_bucket_iam_member" "pipelines_sa_pipeline_assets_bucket_iam" {
  for_each = toset([
    "roles/storage.objectViewer",
    "roles/storage.legacyBucketReader",
  ])
  bucket = google_storage_bucket.pipeline_assets_bucket.name
  member = google_service_account.pipelines_sa.member
  role   = each.key
}

# Give cloud functions SA access to read compiled pipelines from bucket
resource "google_storage_bucket_iam_member" "cloudfunction_sa_pipeline_assets_bucket_iam" {
  for_each = toset([
    "roles/storage.objectViewer",
    "roles/storage.legacyBucketReader",
  ])
  bucket = google_storage_bucket.pipeline_assets_bucket.name
  member = google_service_account.vertex_cloudfunction_sa.member
  role   = each.key
}

# Give cloud functions SA access to use the pipelines SA for triggering pipelines
resource "google_service_account_iam_member" "cloudfunction_sa_can_use_pipelines_sa" {
  service_account_id = google_service_account.pipelines_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = google_service_account.vertex_cloudfunction_sa.member
}

## Project IAM roles ##

# Vertex Pipelines SA project roles
resource "google_project_iam_member" "pipelines_sa_project_roles" {
  for_each = toset(var.pipelines_sa_project_roles)
  project  = var.project_id
  role     = each.key
  member   = google_service_account.pipelines_sa.member
}

# Cloud Function SA project roles
resource "google_project_iam_member" "cloudfunction_sa_project_roles" {
  for_each = toset(var.cloudfunction_sa_project_roles)
  project  = var.project_id
  role     = each.key
  member   = google_service_account.vertex_cloudfunction_sa.member
}
