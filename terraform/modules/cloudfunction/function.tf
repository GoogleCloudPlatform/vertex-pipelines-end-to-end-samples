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

  # List of all the files in the Cloud Function source dir
  cloudfunction_files = fileset(var.source_dir, "*")

  # Get the MD5 of each file in the directory
  file_hashes = [for f in local.cloudfunction_files : filemd5("${var.source_dir}/${f}")]

  # Concatenate hashes and then hash them for an overall hash
  # This method ensures that the hash only changes (and therefore the Cloud Function only re-deploys)
  # when there is an actual change to the source code.
  # Otherwise, ZIP archives change hash e.g. when the absolute paths to files changes, such as in every CI/CD pipeline!
  cloudfunction_hash = md5(join("-", local.file_hashes))
}

data "archive_file" "function_archive" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${var.function_name}.zip"
}

resource "google_storage_bucket_object" "archive" {
  name   = "${data.archive_file.function_archive.output_path}_${local.cloudfunction_hash}.zip"
  bucket = var.source_code_bucket_name
  source = data.archive_file.function_archive.output_path

}

resource "google_cloudfunctions_function" "cloud_functions" {
  project                       = var.project_id
  region                        = var.region
  name                          = var.function_name
  description                   = var.description
  runtime                       = var.runtime
  ingress_settings              = var.ingress_settings
  available_memory_mb           = var.available_memory_mb
  service_account_email         = var.cf_service_account
  vpc_connector                 = var.vpc_connector
  vpc_connector_egress_settings = var.vpc_connector_egress_settings
  timeout                       = var.timeout
  source_archive_bucket         = google_storage_bucket_object.archive.bucket
  source_archive_object         = google_storage_bucket_object.archive.output_name
  trigger_http                  = var.trigger_http


  dynamic "event_trigger" {
    for_each = var.event_trigger == null ? [] : [""]
    content {
      event_type = var.event_trigger.event_type
      resource   = var.event_trigger.resource
      failure_policy {
        retry = var.event_trigger.retry_policy_enabled
      }
    }
  }

  entry_point = var.entry_point

  environment_variables       = var.environment_variables
  build_environment_variables = var.build_environment_variables
  max_instances               = var.max_instances

}
