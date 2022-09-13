inputs = {
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
    # cloudfunction_sa = {
    #   name         = "pipeline-cf-trigger",
    #   display_name = "Vertex Cloud Function trigger SA",
    #   project_roles = [
    #     "roles/aiplatform.user"
    #   ],
    # },
  }
  gcs_buckets_names = {
    pipeline_root_bucket = get_env("PIPELINE_ROOT_BUCKET_NAME")
    # cf_staging_bucket         = "my-cf-staging-bucket"
    # compiled_pipelines_bucket = "my-compiled-pipelines-bucket"
    assets_bucket = get_env("PIPELINE_FILES_BUCKET_NAME")
  }
  vertex_region = get_env("VERTEX_REGION")
  project_id    = get_env("VERTEX_PROJECT_ID")
}
