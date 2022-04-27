<!-- BEGIN_TF_DOCS -->
## Requirements

The following requirements are needed by this module:

- <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) (>= 0.13)

- <a name="requirement_google"></a> [google](#requirement\_google) (~> 4.9.0)

## Providers

The following providers are used by this module:

- <a name="provider_archive"></a> [archive](#provider\_archive)

- <a name="provider_google"></a> [google](#provider\_google) (~> 4.9.0)

## Modules

No modules.

## Resources

The following resources are used by this module:

- [google_cloudfunctions_function.cloud_functions](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloudfunctions_function) (resource)
- [google_storage_bucket_object.archive](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket_object) (resource)
- [archive_file.function_archive](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) (data source)

## Required Inputs

The following input variables are required:

### <a name="input_cf_service_account"></a> [cf\_service\_account](#input\_cf\_service\_account)

Description: The service account (email address) to run the function as.

Type: `string`

### <a name="input_function_name"></a> [function\_name](#input\_function\_name)

Description: Name of the cloud function

Type: `string`

### <a name="input_project_id"></a> [project\_id](#input\_project\_id)

Description: The ID of the project where the cloud function will be deployed.

Type: `string`

### <a name="input_region"></a> [region](#input\_region)

Description: Region of the cloud function.

Type: `string`

### <a name="input_runtime"></a> [runtime](#input\_runtime)

Description: The runtime in which the function will be executed.

Type: `string`

### <a name="input_source_code_bucket_name"></a> [source\_code\_bucket\_name](#input\_source\_code\_bucket\_name)

Description: The name of the bucket to use for staging the Cloud Function code.

Type: `string`

### <a name="input_source_dir"></a> [source\_dir](#input\_source\_dir)

Description: The pathname of the directory which contains the function source code.

Type: `string`

## Optional Inputs

The following input variables are optional (have default values):

### <a name="input_available_memory_mb"></a> [available\_memory\_mb](#input\_available\_memory\_mb)

Description: Memory (in MB), available to the cloud function.

Type: `number`

Default: `null`

### <a name="input_build_environment_variables"></a> [build\_environment\_variables](#input\_build\_environment\_variables)

Description: A set of key/value environment variable pairs available during build time.

Type: `map(string)`

Default: `null`

### <a name="input_description"></a> [description](#input\_description)

Description: Description of the cloud function.

Type: `string`

Default: `null`

### <a name="input_egress_settings"></a> [egress\_settings](#input\_egress\_settings)

Description: The egress settings for the connector, controlling what traffic is diverted through it. Allowed values are ALL\_TRAFFIC and PRIVATE\_RANGES\_ONLY.

Type: `string`

Default: `null`

### <a name="input_entry_point"></a> [entry\_point](#input\_entry\_point)

Description: The name of a method in the function source which will be invoked when the function is executed.

Type: `string`

Default: `null`

### <a name="input_environment_variables"></a> [environment\_variables](#input\_environment\_variables)

Description: A set of key/value environment variable pairs to assign to the function.

Type: `map(string)`

Default: `null`

### <a name="input_event_trigger"></a> [event\_trigger](#input\_event\_trigger)

Description: A source that fires events in response to a condition in another service.

Type:

```hcl
object({
    event_type           = string
    resource             = string
    retry_policy_enabled = bool
  })
```

Default: `null`

### <a name="input_ingress_settings"></a> [ingress\_settings](#input\_ingress\_settings)

Description: The ingress settings for the function. Allowed values are ALLOW\_ALL, ALLOW\_INTERNAL\_AND\_GCLB and ALLOW\_INTERNAL\_ONLY. Changes to this field will recreate the cloud function.

Type: `string`

Default: `null`

### <a name="input_max_instances"></a> [max\_instances](#input\_max\_instances)

Description: The maximum number of parallel executions of the function.

Type: `number`

Default: `null`

### <a name="input_timeout"></a> [timeout](#input\_timeout)

Description: Timeout (in seconds) for the function. Default value is 60 seconds. Cannot be more than 540 seconds.

Type: `number`

Default: `null`

### <a name="input_trigger_http"></a> [trigger\_http](#input\_trigger\_http)

Description: Whether to use HTTP trigger instead of the event trigger.

Type: `bool`

Default: `null`

### <a name="input_vpc_connector"></a> [vpc\_connector](#input\_vpc\_connector)

Description: The VPC Network Connector that this cloud function can connect to. It should be set up as fully-qualified URI. The format of this field is projects//locations//connectors/*.

Type: `string`

Default: `null`

## Outputs

No outputs.
<!-- END_TF_DOCS -->
