<!-- BEGIN_TF_DOCS -->
## Requirements

The following requirements are needed by this module:

- <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) (>= 0.13)

- <a name="requirement_google"></a> [google](#requirement\_google) (~> 4.9.0)

## Providers

The following providers are used by this module:

- <a name="provider_google"></a> [google](#provider\_google) (~> 4.9.0)

## Modules

No modules.

## Resources

The following resources are used by this module:

- [google_cloud_scheduler_job.scheduler_job](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_scheduler_job) (resource)

## Required Inputs

The following input variables are required:

### <a name="input_project_id"></a> [project\_id](#input\_project\_id)

Description: The ID of the project where the cloud scheduler will be created.

Type: `string`

### <a name="input_region"></a> [region](#input\_region)

Description: Region where the scheduler job resides.

Type: `string`

### <a name="input_schedule"></a> [schedule](#input\_schedule)

Description: Describes the schedule on which the job will be executed (UNIX cron format).

Type: `string`

### <a name="input_scheduler_name"></a> [scheduler\_name](#input\_scheduler\_name)

Description: The name of the scheduler job.

Type: `string`

### <a name="input_time_zone"></a> [time\_zone](#input\_time\_zone)

Description: Specifies the time zone to be used in interpreting schedule. The value of this field must be a time zone name from the tz database.

Type: `string`

### <a name="input_topic_id"></a> [topic\_id](#input\_topic\_id)

Description: The Pub/Sub topic to which the cloud scheduler job should publish

Type: `string`

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_attributes"></a> [attributes](#input\_attributes)

Description: Key/value pairs for Pub/Sub attributes. Pubsub message must contain either non-empty data, or at least one attribute.

Type: `map(string)`

Default: `null`

### <a name="input_data"></a> [data](#input\_data)

Description: 'Data' field for the Pub/Sub message. Pub/Sub message must contain either non-empty data, or at least one attribute (or both). A base64-encoded string.

Type: `string`

Default: `null`

### <a name="input_description"></a> [description](#input\_description)

Description: A human-readable description for the scheduler job. This string must not contain more than 500 characters.

Type: `string`

Default: `""`

## Outputs

No outputs.
<!-- END_TF_DOCS -->
