# Vertex Pipelines

This Terraform module contains Infrastructure-as-Code (IaC) for an example deployment.

## Infrastructure Overview

Below is a list of the infrastructure that is created as part of this Terraform module.

- Enabling of relevant Google Cloud APIs
  - *NOTE*: make sure the 'Service Usage' API is enabled (in the console)
- GCS bucket where the compiled pipelines will be published
- GCS bucket for the Cloud Function build
- GCS bucket for the "assets" folder
- Cloud Function for triggering the pipelines
- Pub/Sub topic that is used to trigger the Cloud Function
- Cloud Scheduler jobs for scheduling the pipeline runs
- Service accounts (and suitable IAM roles) for:
  - Vertex Pipelines to execute the pipelines
  - Cloud Function to trigger the pipeline execution
  - Cloud Scheduler to publish messages to the pub/sub topic

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.13 |
| <a name="requirement_google"></a> [google](#requirement\_google) | ~> 4.9.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_google"></a> [google](#provider\_google) | 3.85.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_api_services"></a> [api\_services](#module\_api\_services) | ./modules/apis | n/a |
| <a name="module_assets_bucket_iam"></a> [assets\_bucket\_iam](#module\_assets\_bucket\_iam) | ./modules/bucket_iam | n/a |
| <a name="module_compiled_pipelines_bucket_iam"></a> [compiled\_pipelines\_bucket\_iam](#module\_compiled\_pipelines\_bucket\_iam) | ./modules/bucket_iam | n/a |
| <a name="module_function"></a> [function](#module\_function) | ./modules/function | n/a |
| <a name="module_gcs_buckets"></a> [gcs\_buckets](#module\_gcs\_buckets) | terraform-google-modules/cloud-storage/google | ~> 2.1 |
| <a name="module_pipeline_root_bucket_iam"></a> [pipeline\_root\_bucket\_iam](#module\_pipeline\_root\_bucket\_iam) | ./modules/bucket_iam | n/a |
| <a name="module_pipelines_sa_iam"></a> [pipelines\_sa\_iam](#module\_pipelines\_sa\_iam) | ./modules/sa_iam | n/a |
| <a name="module_pubsub"></a> [pubsub](#module\_pubsub) | terraform-google-modules/pubsub/google | ~> 2.0 |
| <a name="module_scheduler"></a> [scheduler](#module\_scheduler) | ./modules/pubsub_scheduler | n/a |
| <a name="module_service_accounts"></a> [service\_accounts](#module\_service\_accounts) | terraform-google-modules/service-accounts/google | ~> 3.0 |

## Resources

| Name | Type |
|------|------|
| [google_app_engine_application.app](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/app_engine_application) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_api_list"></a> [api\_list](#input\_api\_list) | List of Google Cloud APIs to enable on the project. | `list(string)` | `[]` | no |
| <a name="input_app_engine_region"></a> [app\_engine\_region](#input\_app\_engine\_region) | Region for the App Engine application. | `string` | n/a | yes |
| <a name="input_cloud_function_config"></a> [cloud\_function\_config](#input\_cloud\_function\_config) | Config for the Cloud Function for triggering pipelines, | <pre>object({<br>    name          = string<br>    region        = string<br>    description   = string<br>    vpc_connector = string<br>  })</pre> | n/a | yes |
| <a name="input_cloud_schedulers_config"></a> [cloud\_schedulers\_config](#input\_cloud\_schedulers\_config) | Map of configurations for cloud scheduler jobs (each a different pipeline schedule). | <pre>map(object({<br>    name         = string<br>    region       = string<br>    description  = string<br>    schedule     = string<br>    time_zone    = string<br>    payload_file = string<br>  }))</pre> | `{}` | no |
| <a name="input_gcs_buckets_names"></a> [gcs\_buckets\_names](#input\_gcs\_buckets\_names) | Map of names of GCS buckets to create. | `map(string)` | `{}` | no |
| <a name="input_project_id"></a> [project\_id](#input\_project\_id) | The ID of the project in which to provision resources. | `string` | n/a | yes |
| <a name="input_pubsub_topic_name"></a> [pubsub\_topic\_name](#input\_pubsub\_topic\_name) | Name of the Pub/Sub topic to create for triggering pipelines. | `string` | n/a | yes |
| <a name="input_service_accounts"></a> [service\_accounts](#input\_service\_accounts) | Map of service accounts to create. | <pre>map(object({<br>    name          = string<br>    display_name  = string<br>    project_roles = list(string)<br>  }))</pre> | `{}` | no |
| <a name="input_vertex_region"></a> [vertex\_region](#input\_vertex\_region) | Region for Vertex Pipelines execution. | `string` | n/a | yes |

## Outputs

No outputs.
<!-- END_TF_DOCS -->
