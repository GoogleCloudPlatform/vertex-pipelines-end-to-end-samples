variable "project_id" {
  description = "The ID of the project where the APIs will be enabled"
  type        = string
}

variable "api_list" {
  description = "The list of service APIs to enable"
  type        = list(string)
}
