resource "google_project_service" "api" {
  for_each = toset(var.api_list)

  project = var.project_id
  service = "${each.value}.googleapis.com"

  timeouts {
    create = "30m"
    update = "40m"
  }

  disable_dependent_services = false
  disable_on_destroy         = false
}
