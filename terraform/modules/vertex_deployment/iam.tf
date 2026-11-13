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
  bucket     = google_storage_bucket.pipeline_root_bucket.name
  member     = google_service_account.pipelines_sa.member
  role       = each.key
  depends_on = [time_sleep.wait_for_pipelines_sa]
}

# Give default compute SA access to the staging bucket
# (used by Cloud Build to upload/download source)
data "google_project" "project" {
  project_id = var.project_id
}

resource "google_storage_bucket_iam_member" "cloudbuild_sa_staging_bucket_iam" {
  for_each = toset([
    "roles/storage.objectAdmin",
    "roles/storage.legacyBucketReader",
  ])
  bucket = data.google_storage_bucket.staging_bucket.name
  member = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
  role   = each.key
}

# Give default compute SA project roles needed by Cloud Build
resource "google_project_iam_member" "cloudbuild_sa_project_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/artifactregistry.writer",
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Give Vertex AI Service Agent access to the container images Artifact Registry
# (needed to pull training/prediction images when running pipelines)
resource "google_artifact_registry_repository_iam_member" "vertex_sa_can_access_images_ar" {
  project    = google_artifact_registry_repository.vertex-images.project
  location   = google_artifact_registry_repository.vertex-images.location
  repository = google_artifact_registry_repository.vertex-images.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-aiplatform-cc.iam.gserviceaccount.com"
}

## Project IAM roles ##

# Vertex Pipelines SA project roles
resource "google_project_iam_member" "pipelines_sa_project_roles" {
  for_each   = toset(var.pipelines_sa_project_roles)
  project    = var.project_id
  role       = each.key
  member     = google_service_account.pipelines_sa.member
  depends_on = [time_sleep.wait_for_pipelines_sa]
}
