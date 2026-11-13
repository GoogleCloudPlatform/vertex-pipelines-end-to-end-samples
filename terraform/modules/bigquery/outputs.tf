output "dataset_id" {
  description = "The BigQuery dataset ID."
  value       = google_bigquery_dataset.dataset.dataset_id
}
