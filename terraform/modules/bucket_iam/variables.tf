variable "bucket_name" {
  description = "Name of the GCS bucket that you are providing access to"
  type        = string
}

variable "member" {
  description = "Identity that will be granted the privileges in 'roles'. Requires IAM-style prefix"
  type        = string
}

variable "roles" {
  description = "List of bucket IAM roles that should be granted to the member"
  type        = list(string)
  default     = []
}
