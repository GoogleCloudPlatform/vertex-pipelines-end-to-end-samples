# Give pipelines SA access to create and view objects
# in the pipeline_root bucket
module "pipeline_root_bucket_iam" {
  source      = "./modules/bucket_iam"
  bucket_name = module.gcs_buckets["pipeline_root_bucket"].name
  member      = "serviceAccount:${module.service_accounts["pipelines_sa"].email}"
  roles = [
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
  ]
}

# Give pipelines SA full access to objects in "assets" bucket
module "assets_bucket_iam" {
  source      = "./modules/bucket_iam"
  bucket_name = module.gcs_buckets["assets_bucket"].name
  member      = "serviceAccount:${module.service_accounts["pipelines_sa"].email}"
  roles = [
    "roles/storage.objectAdmin",
  ]
}

# Give cloud functions SA access to read compiled pipelines from bucket
module "compiled_pipelines_bucket_iam" {
  source      = "./modules/bucket_iam"
  bucket_name = module.gcs_buckets["compiled_pipelines_bucket"].name
  member      = "serviceAccount:${module.service_accounts["cloudfunction_sa"].email}"
  roles = [
    "roles/storage.objectViewer",
  ]
}

# Give cloud functions SA access to use the pipelines SA for triggering pipelines
module "pipelines_sa_iam" {
  source          = "./modules/sa_iam"
  service_account = module.service_accounts["pipelines_sa"].service_account.id
  member          = "serviceAccount:${module.service_accounts["cloudfunction_sa"].email}"
  roles = [
    "roles/iam.serviceAccountUser",
  ]
}
