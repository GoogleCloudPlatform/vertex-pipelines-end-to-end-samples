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

variable "project_id" {
  description = "The ID of the project where the cloud function will be deployed."
  type        = string
}

variable "region" {
  description = "Region of the cloud function."
  type        = string
}

variable "function_name" {
  description = "Name of the cloud function"
  type        = string
}

variable "description" {
  description = "Description of the cloud function."
  type        = string
  default     = null
}

variable "runtime" {
  description = "The runtime in which the function will be executed."
  type        = string
}

variable "ingress_settings" {
  description = "The ingress settings for the function. Allowed values are ALLOW_ALL, ALLOW_INTERNAL_AND_GCLB and ALLOW_INTERNAL_ONLY. Changes to this field will recreate the cloud function."
  type        = string
  default     = null
}

variable "vpc_connector" {
  description = "The VPC Network Connector that this cloud function can connect to. It should be set up as fully-qualified URI. The format of this field is projects//locations//connectors/*."
  type        = string
  default     = null
}

variable "vpc_connector_egress_settings" {
  description = "The egress settings for the connector, controlling what traffic is diverted through it. Allowed values are ALL_TRAFFIC and PRIVATE_RANGES_ONLY."
  type        = string
  default     = null
}

variable "event_trigger" {
  description = "A source that fires events in response to a condition in another service."
  type = object({
    event_type           = string
    resource             = string
    retry_policy_enabled = bool
  })

  default = null
}

variable "cf_service_account" {
  description = "The service account (email address) to run the function as."
  type        = string
}

variable "entry_point" {
  description = "The name of a method in the function source which will be invoked when the function is executed."
  type        = string
  default     = null
}
variable "environment_variables" {
  description = "A set of key/value environment variable pairs to assign to the function."
  type        = map(string)
  default     = null
}

variable "build_environment_variables" {
  description = "A set of key/value environment variable pairs available during build time."
  type        = map(string)
  default     = null
}

variable "available_memory_mb" {
  description = "Memory (in MB), available to the cloud function."
  type        = number
  default     = null
}

variable "timeout" {
  description = "Timeout (in seconds) for the function. Default value is 60 seconds. Cannot be more than 540 seconds."
  type        = number
  default     = null
}

variable "trigger_http" {
  description = "Whether to use HTTP trigger instead of the event trigger."
  type        = bool
  default     = null
}

variable "source_code_bucket_name" {
  description = "The name of the bucket to use for staging the Cloud Function code."
  type        = string
}

variable "source_dir" {
  description = "The pathname of the directory which contains the function source code."
  type        = string
}

variable "max_instances" {
  description = "The maximum number of parallel executions of the function."
  type        = number
  default     = null
}
