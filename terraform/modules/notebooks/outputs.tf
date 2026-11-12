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

output "notebooks_sa_email" {
  description = "Email of the Vertex Notebooks service account."
  value       = google_service_account.notebooks_sa.email
}

output "notebook_ids" {
  description = "Map of notebook name to fully-qualified instance ID."
  value       = { for name, nb in google_workbench_instance.notebooks : name => nb.id }
}

output "notebook_proxy_uris" {
  description = "Map of notebook name to Jupyter proxy URI (available once the instance is ACTIVE)."
  value       = { for name, nb in google_workbench_instance.notebooks : name => nb.proxy_uri }
}
