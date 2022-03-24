resource "google_service_account_iam_member" "sa_iam_member" {
  for_each           = toset(var.roles)
  service_account_id = var.service_account
  member             = var.member
  role               = each.key
}
