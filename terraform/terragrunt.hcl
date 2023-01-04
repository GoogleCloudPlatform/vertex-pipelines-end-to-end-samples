locals {
  project_id = get_env("VERTEX_PROJECT_ID")
  region     = get_env("VERTEX_REGION")
}

remote_state {
  backend = "gcs"

  config = {
    bucket   = "${local.project_id}-tfstate-store"
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
        "roles/bigquery.dataEditor",
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
    pipeline_root_bucket      = "${local.project_id}-pipeline-root-bucket"
    cf_staging_bucket         = "${local.project_id}-cf-staging-bucket"
    compiled_pipelines_bucket = "${local.project_id}-compiled-pipelines-bucket"
    assets_bucket             = "${local.project_id}-pipeline-assets-bucket"
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
      payload_file = "${get_path_to_repo_root()}/pipelines/xgboost/training/payloads/dev.json",
    },
  }
}
