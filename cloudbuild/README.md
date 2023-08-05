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

# CI/CD pipelines

## Overview

There are six CI/CD pipelines

1. `pr-checks.yaml` - runs pre-commit checks and unit tests on the custom KFP components, and checks that the ML pipelines (training and prediction) can compile.
1. `trigger-tests.yaml` - runs unit tests for the pipeline trigger script / Cloud Function located in [pipelines/src/pipelines/trigger](/pipelines/src/pipelines/trigger/). If you don't need to change this code, you can ignore this CI/CD pipeline.
1. `e2e-test.yaml` - runs end-to-end tests of the training and prediction pipeline.
1. `release.yaml` - compiles training and prediction pipelines, then copies the compiled pipelines to the chosen GCS destination (versioned by git tag).
1. `terraform-plan.yaml` - Checks the Terraform configuration under `terraform/envs/<env>` (e.g. `terraform/envs/test`), and produces a summary of any proposed changes that will be applied on merge to the main branch.
1. `terraform-apply.yaml` - Applies the Terraform configuration under `terraform/envs/<env>` (e.g. `terraform/envs/test`).

## Setting up the CI/CD pipelines

### Which project should I use for Cloud Build?

We recommend to use a separate `admin` project, since the CI/CD pipelines operate across all the different environments (dev/test/prod).

### Connecting your repository to Google Cloud Build

See the [Google Cloud Documentation](https://cloud.google.com/build/docs/automating-builds/create-manage-triggers) for details on how to link your repository to Cloud Build, and set up triggers.

### Cloud Build service account

Your Cloud Build pipelines will need a service account to use. Create a new service account in the _admin_ project named `cloud-build`. Then, give it these permissions in the different Google Cloud projects:

* dev/test/prod projects - `roles/owner`
* admin project - `roles/logging.logWriter`

## Recommended triggers

### On Pull Request to `main` / `master` branch

Set up a trigger for the `pr-checks.yaml` pipeline.

Set up a trigger for the `e2e-test.yaml` pipeline, and provide substitution values for the following variables:

| Variable | Description | Suggested value |
|---|---|---|
| `_TEST_VERTEX_CMEK_IDENTIFIER` | Optional. ID of the CMEK (Customer Managed Encryption Key) that you want to use for the ML pipeline runs in the E2E tests as part of the CI/CD pipeline with the format `projects/my-project/locations/my-region/keyRings/my-kr/cryptoKeys/my-key` | Leave blank |
| `_TEST_VERTEX_LOCATION` | The Google Cloud region where you want to run the ML pipelines in the E2E tests as part of the CI/CD pipeline. | Your chosen Google Cloud region |
| `_TEST_VERTEX_NETWORK` | Optional. The full name of the Compute Engine network to which the ML pipelines should be peered during the E2E tests as part of the CI/CD pipeline with the format `projects/<project number>/global/networks/my-vpc` |
| `_TEST_VERTEX_PIPELINE_ROOT` | The GCS folder (i.e. path prefix) that you want to use for the pipeline artifacts and for passing data between stages in the pipeline. Used during the pipeline runs in the E2E tests as part of the CI/CD pipeline. | `gs://<Project ID for dev environment>-pl-root` |
| `_TEST_VERTEX_PROJECT_ID` | Google Cloud project ID in which you want to run the ML pipelines in the E2E tests as part of the CI/CD pipeline. | Project ID for the DEV environment |
| `_TEST_VERTEX_SA_EMAIL` | Email address of the service account you want to use to run the ML pipelines in the E2E tests as part of the CI/CD pipeline. | `vertex-pipelines@<Project ID for dev environment>.iam.gserviceaccount.com` |
| `_TEST_ENABLE_PIPELINE_CACHING` | Override the default caching behaviour of the ML pipelines. Leave blank to use the default caching behaviour. | `False` |

We recommend to enable comment control for this trigger (select `Required` under `Comment Control`). This will mean that the end-to-end tests will only run once a repository collaborator or owner comments `/gcbrun` on the pull request.
This will help to avoid unnecessary runs of the ML pipelines while a Pull Request is still being worked on, as they can take a long time (and can be expensive to run on every Pull Request!)

Set up three triggers for `terraform-plan.yaml` - one for each of the dev/test/prod environments. Set the Cloud Build substitution variables as follows:

| Environment | Cloud Build substitution variables |
|---|---|
| dev | **\_PROJECT_ID**=\<Google Cloud Project ID for the dev environment><br>**\_REGION**=\<Google Cloud region to use for the dev environment><br>**\_ENV_DIRECTORY**=terraform/envs/dev |
| test | **\_PROJECT_ID**=\<Google Cloud Project ID for the test environment><br>**\_REGION**=\<Google Cloud region to use for the test environment><br>**\_ENV_DIRECTORY**=terraform/envs/test |
| prod | **\_PROJECT_ID**=\<Google Cloud Project ID for the prod environment><br>**\_REGION**=\<Google Cloud region to use for the prod environment><br>**\_ENV_DIRECTORY**=terraform/envs/prod |

### On push of new tag

Set up a trigger for the `release.yaml` pipeline, and provide substitution values for the following variables:

| Variable | Description | Suggested value |
|---|---|---|
| `_PIPELINE_PUBLISH_AR_PATHS` | The (space separated) Artifact Registry repositories (plural!) where the compiled pipelines will be copied to - one for each environment (dev/test/prod). | `https://europe-west2-kfp.pkg.dev/<Project ID for dev environment>/vertex-pipelines https://europe-west2-kfp.pkg.dev/<Project ID for test environment>/vertex-pipelines https://europe-west2-kfp.pkg.dev/<Project ID for prod environment>/vertex-pipelines` |

### On merge to `main` / `master` branch

Set up three triggers for `terraform-apply.yaml` - one for each of the dev/test/prod environments. Set the Cloud Build substitution variables as follows:

| Environment | Cloud Build substitution variables |
|---|---|
| dev | **\_PROJECT_ID**=\<Google Cloud Project ID for the dev environment><br>**\_REGION**=\<Google Cloud region to use for the dev environment><br>**\_ENV_DIRECTORY**=terraform/envs/dev |
| test | **\_PROJECT_ID**=\<Google Cloud Project ID for the test environment><br>**\_REGION**=\<Google Cloud region to use for the test environment><br>**\_ENV_DIRECTORY**=terraform/envs/test |
| prod | **\_PROJECT_ID**=\<Google Cloud Project ID for the prod environment><br>**\_REGION**=\<Google Cloud region to use for the prod environment><br>**\_ENV_DIRECTORY**=terraform/envs/prod |
