resource "google_cloud_scheduler_job" "scheduler_job" {
  name        = var.scheduler_name
  project     = var.project_id
  region      = var.region
  description = var.description
  schedule    = var.schedule
  time_zone   = var.time_zone

  pubsub_target {
    topic_name = var.topic_id
    attributes = var.attributes
    data       = var.data
  }

}
