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

variable "scheduler_name" {
  description = "The name of the scheduler job."
  type        = string
}
variable "project_id" {
  description = "The ID of the project where the cloud scheduler will be created."
  type        = string
}

variable "region" {
  description = "Region where the scheduler job resides."
  type        = string
}


variable "description" {
  description = "A human-readable description for the scheduler job. This string must not contain more than 500 characters."
  type        = string
  default     = ""
}

variable "schedule" {
  description = "Describes the schedule on which the job will be executed (UNIX cron format)."
  type        = string
}

variable "time_zone" {
  description = "Specifies the time zone to be used in interpreting schedule. The value of this field must be a time zone name from the tz database."
  type        = string
}

variable "topic_id" {
  description = "The Pub/Sub topic to which the cloud scheduler job should publish"
  type        = string
}

variable "attributes" {
  description = "Key/value pairs for Pub/Sub attributes. Pubsub message must contain either non-empty data, or at least one attribute."
  type        = map(string)
  default     = null
}

variable "data" {
  description = "'Data' field for the Pub/Sub message. Pub/Sub message must contain either non-empty data, or at least one attribute (or both). A base64-encoded string."
  type        = string
  default     = null
}
