<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.13 |
| <a name="requirement_google"></a> [google](#requirement\_google) | ~> 4.9.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_google"></a> [google](#provider\_google) | ~> 4.9.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [google_service_account_iam_member.sa_iam_member](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/service_account_iam_member) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_member"></a> [member](#input\_member) | Identity that will be granted the privileges in 'roles'. Requires IAM-style prefix | `string` | n/a | yes |
| <a name="input_roles"></a> [roles](#input\_roles) | List of service account IAM roles that should be granted to the member | `list(string)` | `[]` | no |
| <a name="input_service_account"></a> [service\_account](#input\_service\_account) | Service account (fully-qualified ID) that you are giving permissions to access | `string` | n/a | yes |

## Outputs

No outputs.
<!-- END_TF_DOCS -->
