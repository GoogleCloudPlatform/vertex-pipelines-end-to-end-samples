<!--
Copyright 2022 Google LLC

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

## Deployment into blank Google Cloud Project

The section below details how to deploy the infrastructure into a blank Google Cloud Project

###  Prerequisites

- [Terraform](https://www.terraform.io/docs)
- [Terragrunt](https://terragrunt.gruntwork.io/docs/)

###  Deployment

Given the `env.sh` exists in the repository root and is populated with suitable values for the required variables, run `make deploy-infra` from the repository root to initialise terraform and deploy all the required infrastructure as defined in this folder.

Once the deployment is completed, pipelines can be ran manually or automatically on a schedule as defined by the `cloud_schedulers_config` in the `terragrunt.hcl` file.

The terragrunt configuration automatically creates a GCS bucket for storing the terraform state. For more information see terragrunt [remote_state](https://terragrunt.gruntwork.io/docs/reference/config-blocks-and-attributes/#remote_state).  

###  Clean up

To destroy the deployed infrastructure defined in this directory, run `make destroy-infra` from the repository root.
