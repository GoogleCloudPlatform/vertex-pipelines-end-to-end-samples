locals {
  project_id = get_env("VERTEX_PROJECT_ID")
  region     = get_env("VERTEX_REGION")
}

remote_state {
  backend = "gcs"

  config = {
    bucket   = "tf-state-bucket-${local.project_id}" # TODO: change to tf-state suffix
    prefix   = "module/${path_relative_to_include()}"
    project  = local.project_id
    location = local.region
  }

  generate = {
    path      = "./backend.tf"
    if_exists = "overwrite"
  }
}

inputs = {
  vertex_region     = local.region
  project_id        = local.project_id
  app_engine_region = "europe-west2"  # There are no cloud functions in europe-west4
  bigquery_location = "EU"
  pubsub_topic_name = "vertex-pipelines-trigger"

  api_list = [
    "storage-api",
    "aiplatform",
    "bigquery",
    "cloudscheduler",
    "cloudfunctions",
    "pubsub",
    "iam",
    "appengine",
    "cloudbuild",
  ]

  service_accounts = {
    pipelines_sa = {
      name         = get_env("VERTEX_SA_NAME"),
      display_name = "Vertex Pipelines SA",
      project_roles = [
        "roles/aiplatform.user",
        "roles/bigquery.jobUser",
        "roles/bigquery.dataEditor", # Added by JAN - Getting 403 when trying to access taxi_trips table inside dataset: https://console.cloud.google.com/vertex-ai/locations/europe-west4/pipelines/runs/xgboost-train-pipeline-20220906174714?project=dt-jan-sandbox-dev AND https://stackoverflow.com/questions/52533796/unable-to-run-query-against-bigquery-permission-error-403
      ],
    },
    cloudfunction_sa = {
      name         = "pipeline-cf-trigger",
      display_name = "Vertex Cloud Function trigger SA",
      project_roles = [
        "roles/aiplatform.user"
      ],
    },
  }
  gcs_buckets_names = {
    pipeline_root_bucket      = get_env("PIPELINE_ROOT_BUCKET_NAME")
    cf_staging_bucket         = "${local.project_id}-cf-staging-bucket"
    compiled_pipelines_bucket = "${local.project_id}-compiled-pipelines-bucket"
    assets_bucket             = get_env("PIPELINE_FILES_BUCKET_NAME")
  }
  cloud_function_config = {
    name          = "vertex-pipelines-trigger",
    region        = "europe-west2",  # There are no cloud functions in europe-west4
    description   = "Vertex Pipeline trigger function",
    vpc_connector = null,
  }

  cloud_schedulers_config = {
    training = {
      name         = "training-pipeline-trigger",
      region       = "europe-west2",  # There are no cloud functions in europe-west4
      description  = "Trigger my training pipeline in Vertex",
      schedule     = "0 0 * * 0",
      time_zone    = "UTC",
      payload_file = "../pipelines/xgboost/training/payloads/dev.json",  # TODO: Think about this, the attributes.template_path references local file and not gcs location
    },
  }
}
