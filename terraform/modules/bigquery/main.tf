resource "google_bigquery_dataset" "dataset" {
  dataset_id                 = var.dataset_id
  project                    = var.project_id
  location                   = var.region
  description                = var.description
  delete_contents_on_destroy = var.delete_contents_on_destroy

  labels = var.labels
}
