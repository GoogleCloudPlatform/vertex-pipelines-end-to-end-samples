# Google Cloud APIs to enable
module "api_services" {
  source     = "./modules/apis"
  project_id = var.project_id
  api_list   = var.api_list
}

# Service Accounts
module "service_accounts" {
  for_each      = var.service_accounts
  source        = "terraform-google-modules/service-accounts/google"
  version       = "~> 3.0"
  project_id    = var.project_id
  display_name  = each.value.display_name
  names         = [each.value.name]
  project_roles = [for binding in each.value.project_roles : "${var.project_id}=>${binding}"]
  depends_on    = [module.api_services]
}

# GCS buckets
module "gcs_buckets" {
  for_each   = var.gcs_buckets_names
  source     = "terraform-google-modules/cloud-storage/google"
  version    = "~> 2.1"
  prefix     = ""
  project_id = var.project_id
  names      = [each.value]
  depends_on = [module.api_services]
}

# Pub/Sub topic (for triggering pipelines)
module "pubsub" {
  source     = "terraform-google-modules/pubsub/google"
  version    = "~> 2.0"
  project_id = var.project_id
  topic      = var.pubsub_topic_name
  depends_on = [module.api_services]
}

# Cloud function (for triggering pipelines)
module "function" {
  source                  = "./modules/function"
  project_id              = var.project_id
  region                  = var.cloud_function_config.region
  function_name           = var.cloud_function_config.name
  description             = lookup(var.cloud_function_config, "description", null)
  source_dir              = "../pipelines/trigger"
  source_code_bucket_name = module.gcs_buckets["cf_staging_bucket"].name
  runtime                 = "python39"
  entry_point             = "cf_handler"
  cf_service_account      = module.service_accounts["cloudfunction_sa"].email
  vpc_connector           = lookup(var.cloud_function_config, "vpc_connector", null)
  event_trigger = {
    event_type           = "google.pubsub.topic.publish",
    resource             = module.pubsub.id
    retry_policy_enabled = false
  }
  environment_variables = {
    VERTEX_LOCATION      = var.vertex_region
    VERTEX_PIPELINE_ROOT = "gs://${module.gcs_buckets["pipeline_root_bucket"].name}"
    VERTEX_PROJECT_ID    = var.project_id
    VERTEX_SA_EMAIL      = module.service_accounts["pipelines_sa"].email
  }
  depends_on = [module.api_services]
}

# Cloud Scheduler jobs (for triggering pipelines)
module "scheduler" {
  for_each       = var.cloud_schedulers_config
  source         = "./modules/pubsub_scheduler"
  project_id     = var.project_id
  region         = each.value.region
  scheduler_name = each.value.name
  description    = lookup(each.value, "description", null)
  schedule       = each.value.schedule
  time_zone      = lookup(each.value, "time_zone", "UTC")
  topic_id       = module.pubsub.id
  attributes     = jsondecode(file(each.value.payload_file)).attributes
  data           = base64encode(jsonencode(jsondecode(file(each.value.payload_file)).data))
  depends_on     = [module.api_services, google_app_engine_application.app]
}

# App Engine application is required for Cloud Scheduler jobs
resource "google_app_engine_application" "app" {
  project     = var.project_id
  location_id = var.app_engine_region
  depends_on  = [module.api_services]
}
