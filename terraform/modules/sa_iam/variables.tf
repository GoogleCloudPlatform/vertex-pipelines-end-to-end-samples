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

variable "service_account" {
  description = "Service account (fully-qualified ID) that you are giving permissions to access"
  type        = string
}

variable "member" {
  description = "Identity that will be granted the privileges in 'roles'. Requires IAM-style prefix"
  type        = string
}

variable "roles" {
  description = "List of service account IAM roles that should be granted to the member"
  type        = list(string)
  default     = []
}
