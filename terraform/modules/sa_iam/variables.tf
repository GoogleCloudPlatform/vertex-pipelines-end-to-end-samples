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
