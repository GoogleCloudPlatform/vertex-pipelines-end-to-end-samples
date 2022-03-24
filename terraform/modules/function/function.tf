data "archive_file" "function_archive" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "${var.function_name}.zip"
}

resource "google_storage_bucket_object" "archive" {
  name   = "${data.archive_file.function_archive.output_path}_${data.archive_file.function_archive.output_md5}.zip"
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
  vpc_connector_egress_settings = var.egress_settings
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
