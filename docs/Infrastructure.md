<!-- 
Copyright 2023 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
 -->
# Infrastructure

We recommend using [`tfswitch`](https://tfswitch.warrensbox.com/) to automatically choose and download an appropriate version for you (run `tfswitch` from the [`terraform/envs/dev`](terraform/envs/dev/) directory).

The cloud infrastructure is managed using Terraform and is defined in the [`terraform`](terraform) directory. There are three Terraform modules defined in [`terraform/modules`](terraform/modules):

- `cloudfunction` - deploys a (Pub/Sub-triggered) Cloud Function from local source code
- `scheduled_pipelines` - deploys Cloud Scheduler jobs that will trigger Vertex Pipeline runs (via the above Cloud Function)
- `vertex_deployment` - deploys Cloud infrastructure required for running Vertex Pipelines, including enabling APIs, creating buckets, Artifact Registry repos, service accounts, and IAM permissions.

There is a Terraform configuration for each environment (dev/test/prod) under [`terraform/envs`](terraform/envs/).

## Schedule pipelines

Terraform is used to deploy Cloud Scheduler jobs that trigger the Vertex Pipeline runs. This is done by the CI/CD pipelines (see section below on CI/CD).

To schedule pipelines into an environment, you will need to provide the `cloud_schedulers_config` variable to the Terraform configuration for the relevant environment. 
You can find an example of this configuration in [`terraform/modules/scheduled_pipelines/scheduled_jobs.auto.tfvars.example`](terraform/modules/scheduled_pipelines/scheduled_jobs.auto.tfvars.example). 
Copy this example file into the relevant directory for your environment (e.g. `terraform/envs/dev` for the dev environment) and remove the `.example` suffix. 
Adjust the configuration file as appropriate.

## Tear down infrastructure

To tear down the infrastructure you have created with Terraform, run these commands:

```bash
make undeploy env=dev VERTEX_PROJECT_ID=<DEV PROJECT ID>
```
