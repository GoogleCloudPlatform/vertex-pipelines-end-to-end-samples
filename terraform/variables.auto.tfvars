project_id = "my-project-id"

api_list = [
  "storage-api",
  "aiplatform",
  "cloudscheduler",
  "cloudfunctions",
  "pubsub",
  "iam",
  "appengine",
  "cloudbuild",
]

app_engine_region = "europe-west4"
vertex_region     = "europe-west4"

service_accounts = {
  pipelines_sa = {
    name         = "vertex-pipelines",
    display_name = "Vertex Pipelines SA",
    project_roles = [
      "roles/aiplatform.user"
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
  pipeline_root_bucket      = "my-pipeline-root-bucket"
  cf_staging_bucket         = "my-cf-staging-bucket"
  compiled_pipelines_bucket = "my-compiled-pipelines-bucket"
  assets_bucket             = "my-assets-bucket"
}

pubsub_topic_name = "vertex-pipelines-trigger"

cloud_function_config = {
  name          = "vertex-pipelines-trigger",
  region        = "europe-west4",
  description   = "Vertex Pipeline trigger function",
  vpc_connector = null,
}

cloud_schedulers_config = {
  training = {
    name         = "training-pipeline-trigger",
    region       = "europe-west4",
    description  = "Trigger my training pipeline in Vertex",
    schedule     = "0 0 * * 0",
    time_zone    = "UTC",
    payload_file = "../pipelines/xgboost/training/payloads/dev.json",
  },
}
