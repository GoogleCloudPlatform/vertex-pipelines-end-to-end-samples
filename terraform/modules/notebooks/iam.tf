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

# Project roles for the notebooks service account (Vertex, BQ, GCS, AR, logging)
resource "google_project_iam_member" "notebooks_sa_project_roles" {
  for_each   = toset(var.notebooks_sa_project_roles)
  project    = var.project_id
  role       = each.key
  member     = google_service_account.notebooks_sa.member
  depends_on = [time_sleep.wait_for_notebooks_sa]
}

# Allow notebook owners to use the notebooks SA on the VM (iam.serviceAccounts.actAs).
# Workbench requires each instance_owner to have this before the instance is created.
resource "google_service_account_iam_member" "notebook_owners_can_act_as_sa" {
  for_each = {
    for name, nb in var.notebooks : name => nb
    if nb.owner != ""
  }

  service_account_id = google_service_account.notebooks_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "user:${each.value.owner}"
  depends_on         = [time_sleep.wait_for_notebooks_sa]
}

# IAM bindings are not always visible immediately after create.
resource "time_sleep" "wait_for_notebook_owner_iam" {
  count           = length([for nb in var.notebooks : nb if nb.owner != ""]) > 0 ? 1 : 0
  depends_on      = [google_service_account_iam_member.notebook_owners_can_act_as_sa]
  create_duration = "30s"
}
