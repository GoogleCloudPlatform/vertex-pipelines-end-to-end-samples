
terraform {
  required_version = ">= 0.13"
  required_providers {

    google = {
      source  = "hashicorp/google"
      version = "~> 4.9.0"
    }
  }

  # Terraform state stored in GCS
  backend "gcs" {
    bucket = "my-tfstate-bucket" # Change this
    prefix = "/path/to/tfstate"  # Change this
  }
}


# Cloud Scheduler jobs (for triggering pipelines)
module "scheduler" {
  for_each       = var.cloud_schedulers_config
  source         = "../../terraform/modules/pubsub_scheduler"
  project_id     = var.project_id
  region         = each.value.region
  scheduler_name = each.value.name
  description    = lookup(each.value, "description", null)
  schedule       = each.value.schedule
  time_zone      = lookup(each.value, "time_zone", "UTC")
  topic_id       = "projects/${var.project_id}/topics/${var.pubsub_topic_name}"
  attributes     = jsondecode(file(each.value.payload_file)).attributes
  data           = base64encode(jsonencode(jsondecode(file(each.value.payload_file)).data))
}
