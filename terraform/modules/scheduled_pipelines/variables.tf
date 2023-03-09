/**
 * Copyright 2022 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

variable "name" {
  description = "Name of the Cloud Scheduler job."
  type        = string
}

variable "project_id" {
  description = "ID of the project where the Cloud Scheduler job resides."
  type        = string
}

variable "region" {
  description = "Region where the Cloud Scheduler job resides."
  type        = string
}

variable "description" {
  description = "A human-readable description for the Cloud Scheduler job. This string must not contain more than 500 characters."
  type        = string
}

variable "schedule" {
  description = "Describes the schedule on which the job will be executed using cron syntax."
  type        = string
}

variable "time_zone" {
  description = "Specifies the time zone to be used in interpreting schedule. The value of this field must be a time zone name from the tz database."
  type        = string
  default     = "UTC"
}

variable "topic_name" {
  description = "The full resource name for the Cloud Pub/Sub topic to which messages will be published when a job is delivered. ~>NOTE: The topic name must be in the same format as required by PubSub's PublishRequest.name, e.g. projects/my-project/topics/my-topic"
  type        = string
}

variable "template_path" {
  description = "GCS path to the compiled KFP pipeline to be triggered by the Cloud Scheduler job."
  type        = string
}

variable "enable_caching" {
  description = "Whether to turn on caching for the Vertex Pipeline runs. If this is not set, defaults to the compile time settings, which are True for all tasks by default, while users may specify different caching options for individual tasks. If this is set, the setting applies to all tasks in the pipeline."
  type        = bool
  default     = null
}

variable "pipeline_parameters" {
  description = "The mapping from runtime parameter names to its values that control the Vertex Pipeline run."
  type        = map(any)
  default     = {}
}
