variable "project_id" {
  description = "The ID of the project in which to provision resources."
  type        = string
}

variable "pubsub_topic_name" {
  description = "Name of the Pub/Sub topic to use for triggering pipelines."
  type        = string
}

variable "cloud_schedulers_config" {
  description = "Map of configurations for cloud scheduler jobs (each a different pipeline schedule)."
  type = map(object({
    name         = string
    region       = string
    description  = string
    schedule     = string
    time_zone    = string
    payload_file = string
  }))
  default = {}
}
