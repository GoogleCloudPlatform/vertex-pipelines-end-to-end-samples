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

# CI/CD pipelines

## Overview

There are five CI/CD pipelines

1. `pr-checks.yaml` - runs pre-commit checks and unit tests on the custom KFP components, and checks that the ML pipelines (training and prediction) can compile.
1. `e2e-test.yaml` - copies the "assets" folders to the chosen GCS destination (versioned by git commit hash) and runs end-to-end tests of the training and prediction pipeline.
1. `release.yaml` - compiles training and prediction pipelines, then copies the compiled pipelines and their respective "assets" folders to the chosen GCS destination (versioned by git tag).
1. `terraform-plan.yaml` - Checks the Terraform configuration under `terraform/envs/<env>` (e.g. `terraform/envs/test`), and produces a summary of any proposed changes that will be applied on merge to the main branch.
1. `terraform-apply.yaml` - Applies the Terraform configuration under `terraform/envs/<env>` (e.g. `terraform/envs/test`).

## Setting up the CI/CD pipelines

### Which project should I use for Cloud Build?

It is recommended to use a separate `admin` project, so that your dev/test/prod projects are treated identically.

### Connecting your repository to Google Cloud Build

See the [Google Cloud Documentation](https://cloud.google.com/build/docs/automating-builds/create-manage-triggers) for details on how to link your repository to Cloud Build, and set up triggers.

### Cloud Build service accounts

Your Cloud Build pipelines will need a service account to use. We recommend the following service accounts to be created in the _admin_ project:

| Service account name | Pipeline(s) | Permissions |
|---|---|---|
| `cloudbuild-prchecks` | `pr-checks.yaml` | `roles/logging.logWriter` (`admin` project) |
| `cloudbuild-e2e-test` | `e2e-test.yaml` | `roles/logging.logWriter` (`admin` project)<br>`roles/storage.admin` (`dev` project)<br>`roles/aiplatform.user` (`dev` project)<br>`roles/iam.serviceAccountUser` (`dev` project) |
| `cloudbuild-release` | `release.yaml` | `roles/logging.logWriter` (`admin` project)<br>`roles/storage.admin` (`dev` project)<br>`roles/storage.admin` (`test` project)<br>`roles/storage.admin` (`prod` project) |
| `terraform-dev` | `terraform-plan.yaml` (dev)<br>`terraform-apply.yaml` (dev) | `roles/logging.logWriter` (`admin` project)<br>`roles/owner` (`dev` project)<br>`roles/storage.admin` (`dev` project) |
| `terraform-test` | `terraform-plan.yaml` (test)<br>`terraform-apply.yaml` (test) | `roles/logging.logWriter` (`admin` project)<br>`roles/owner` (`test` project)<br>`roles/storage.admin` (`test` project) |
| `terraform-prod` | `terraform-plan.yaml` (prod)<br>`terraform-apply.yaml` (prod) | `roles/logging.logWriter` (`admin` project)<br>`roles/owner` (`prod` project)<br>`roles/storage.admin` (`prod` project) |

## Recommended triggers

Use the service accounts specified above for these triggers respectively.

### On Pull Request to `main` / `master` branch

Set up a trigger for the `pr-checks.yaml` pipeline, and provide a substitution value for the variable `_PIPELINE_TEMPLATE` (either `xgboost` or `tensorflow`, depending which pipelines you are using).

Set up a trigger for the `e2e-test.yaml` pipeline, and provide substitution values for the following variables:

| Variable | Description | Suggested value |
|---|---|---|
| `_PIPELINE_PUBLISH_GCS_PATH` | The GCS folder (i.e. path prefix) where the pipeline files will be copied to. See the [Assets](../README.md#assets) section of the main README for more information. | `gs://<Project ID for dev environment>-pl-assets/e2e-tests` |
| `_PIPELINE_TEMPLATE` | The set of pipelines in the repo that you would like to use - i.e. the subfolder under `pipelines` where your pipelines live. | Currently, can be either `xgboost` or `tensorflow`. |
| `_TEST_VERTEX_CMEK_IDENTIFIER` | Optional. ID of the CMEK (Customer Managed Encryption Key) that you want to use for the ML pipeline runs in the E2E tests as part of the CI/CD pipeline with the format `projects/my-project/locations/my-region/keyRings/my-kr/cryptoKeys/my-key` | Leave blank |
| `_TEST_VERTEX_LOCATION` | The Google Cloud region where you want to run the ML pipelines in the E2E tests as part of the CI/CD pipeline. | Your chosen Google Cloud region |
| `_TEST_VERTEX_NETWORK` | Optional. The full name of the Compute Engine network to which the ML pipelines should be peered during the E2E tests as part of the CI/CD pipeline with the format `projects/<project number>/global/networks/my-vpc` |
| `_TEST_VERTEX_PIPELINE_ROOT` | The GCS folder (i.e. path prefix) that you want to use for the pipeline artifacts and for passing data between stages in the pipeline. Used during the pipeline runs in the E2E tests as part of the CI/CD pipeline. | `gs://<Project ID for dev environment>-pl-root` |
| `_TEST_VERTEX_PROJECT_ID` | Google Cloud project ID in which you want to run the ML pipelines in the E2E tests as part of the CI/CD pipeline. | Project ID for the dev environment |
| `_TEST_VERTEX_SA_EMAIL` | Email address of the service account you want to use to run the ML pipelines in the E2E tests as part of the CI/CD pipeline. | `vertex-pipelines@<Project ID for dev environment>.iam.gserviceaccount.com` |
| `_TEST_TRAIN_STATS_GCS_PATH` | GCS path to use for storing the statistics computed about the training dataset used in the training pipeline. | `gs://<Project ID for dev environment>-pl-root/train_stats/train.stats` |
| `_TEST_ENABLE_PIPELINE_CACHING` | Override the default caching behaviour of the ML pipelines. Leave blank to use the default caching behaviour. | `False` |

We recommend to enable comment control for this trigger (select `Required` under `Comment Control`). This will mean that the end-to-end tests will only run once a repository collaborator or owner comments `/gcbrun` on the pull request.
This will help to avoid unnecessary runs of the ML pipelines while a Pull Request is still being worked on, as they can take a long time (and can be expensive to run on every pull request!)

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
| `_PIPELINE_PUBLISH_GCS_PATHS` | The (space separated) GCS folders (plural!) where the pipeline files (compiled pipelines + pipeline assets) will be copied to. See the [Assets](../README.md#assets) section of the main README for more information. | `gs://<Project ID for dev environment>-pl-assets gs://<Project ID for test environment>-pl-assets gs://<Project ID for prod environment>-pl-assets` |
| `_PIPELINE_TEMPLATE` | The set of pipelines in the repo that you would like to use - i.e. the subfolder under `pipelines` where your pipelines live. | Currently, can be either `xgboost` or `tensorflow`. |

### On merge to `main` / `master` branch

Set up three triggers for `terraform-apply.yaml` - one for each of the dev/test/prod environments. Set the Cloud Build substitution variables as follows:

| Environment | Cloud Build substitution variables |
|---|---|
| dev | **\_PROJECT_ID**=\<Google Cloud Project ID for the dev environment><br>**\_REGION**=\<Google Cloud region to use for the dev environment><br>**\_ENV_DIRECTORY**=terraform/envs/dev |
| test | **\_PROJECT_ID**=\<Google Cloud Project ID for the test environment><br>**\_REGION**=\<Google Cloud region to use for the test environment><br>**\_ENV_DIRECTORY**=terraform/envs/test |
| prod | **\_PROJECT_ID**=\<Google Cloud Project ID for the prod environment><br>**\_REGION**=\<Google Cloud region to use for the prod environment><br>**\_ENV_DIRECTORY**=terraform/envs/prod |
