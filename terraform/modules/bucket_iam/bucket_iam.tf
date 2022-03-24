resource "google_storage_bucket_iam_member" "bucket_iam_member" {
  for_each = toset(var.roles)
  bucket   = var.bucket_name
  member   = var.member
  role     = each.key
}
