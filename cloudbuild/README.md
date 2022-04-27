# CI/CD pipelines

## Overview

There are four CI/CD pipelines

1. `pr-checks.yaml` - runs pre-commit checks and unit tests on the custom KFP components, and checks that the ML pipelines (training and prediction) can compile.
1. `release.yaml` - compiles training and prediction pipelines, then copies the compiled pipelines and their respective "assets" folders to GCS destinations in the test and prod environments.
3. `terraform-plan.yaml` - Checks the Terraform configuration under `envs/<env>` (i.e. `envs/test` or `envs/prod`), and produces a summary of any proposed changes that will be applied on merge to the main branch. Out of the box, this just includes Cloud Scheduler jobs used to schedule your ML pipelines.
4. `terraform-apply.yaml` - Applies the Terraform configuration under `envs/<env>` (i.e. `envs/test` or `envs/prod`). Out of the box, this just includes Cloud Scheduler jobs used to schedule your ML pipelines.

The last two assume you have already set up your infrastructure separately (GCS buckets, service accounts, IAM, Pub/Sub topic, and Cloud Function). If not, you can use the Terraform modules under [`terraform/modules`](../terraform) to do this.

## Setting up the CI/CD pipelines

See the [Google Cloud Documentation](https://cloud.google.com/build/docs/automating-builds/create-manage-triggers) for details on how to link your repository to Cloud Build, and set up triggers.

## Variable substitutions

Below is a table detailing the variable substitutions you will need to set up in your triggers:

| Variable name                 | Description                                                                                                                                                                                                                 | Example value                                                            |
|-------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |--------------------------------------------------------------------------|
| _PIPELINE_PUBLISH_GCS_PATH | The GCS folder (i.e. path prefix) in the build/CI/CD environment where the pipeline files will be copied to. See the [Assets](../README.md#assets) section of the main README for more information.                                     | gs://my-cicd-bucket/pipelines                                            |
| _PIPELINE_TEMPLATE            | The set of pipelines in the repo that you would like to use - i.e. the subfolder under `pipelines` where you pipelines live. Currently, can be either `xgboost` or `tensorflow`.                                            | xgboost                                                                  |
| _TEST_PAYLOAD                 | The file name of the JSON payload that you want to use for the ML pipeline runs in the E2E tests.                                                                                                                    | test.json                                                                |
| _TEST_VERTEX_CMEK_IDENTIFIER  | Optional. ID of the CMEK (Customer Managed Encryption Key) that you want to use for the ML pipeline runs in the E2E tests as part of the CI/CD pipeline.                                                             | projects/my-project/locations/my-region/keyRings/my-kr/cryptoKeys/my-key |
| _TEST_VERTEX_LOCATION         | The GCP region where you want to run the ML pipelines in the E2E tests as part of the CI/CD pipeline.                                                                                                                | europe-west4                                                             |
| _TEST_VERTEX_NETWORK          | Optional. The full name of the Compute Engine network to which the ML pipelines should be peered during the E2E tests as part of the CI/CD pipeline.                                                                 | projects/12345/global/networks/myVPC                                     |
| _TEST_VERTEX_PIPELINE_ROOT    | The GCS folder (i.e. path prefix) that you want to use for the pipeline artifacts and for passing data between stages in the pipeline. Used during the pipeline runs in the E2E tests as part of the CI/CD pipeline. | gs://my_pipeline_root_bucket/pipeline_root                               |
| _TEST_VERTEX_PROJECT_ID       | GCP Project ID in which you want to run the ML pipelines in the E2E tests as part of the CI/CD pipeline.                                                                                                             | my-first-gcp-project                                                     |
| _TEST_VERTEX_SA_EMAIL         | Email address of the service account you want to use to run the ML pipelines in the E2E tests as part of the CI/CD pipeline.                                                                                         | vertex-pipeline-runner@my-first-gcp-project.iam.gserviceaccount.com      |
| _ENV_DIRECTORY | Terraform configuration directory for the environment to which you want to deploy - used in the Terraform Cloud Build pipelines. Value will be either `envs/test` or `envs/prod` (defaults to `envs/test`). | `envs/test` |

## Recommended triggers

### On Pull Request to `main` / `master` branch

Set up a trigger for the `pr-checks.yaml` pipeline, and provide a substitution value for the variable `_PIPELINE_TEMPLATE` (either `xgboost` or `tensorflow`).

Set up two triggers for `terraform-plan.yaml`:
  - One for the test environment. Set the substitution value for the variable `_ENV_DIRECTORY` to `envs/test`.
  - One for the prod environment. Set the substitution value for the variable `_ENV_DIRECTORY` to `envs/prod`.

### On push of new tag

Set up a trigger for the `release.yaml` pipeline, and provide substitution values for the following variables (described in the table above):

- `_PIPELINE_PUBLISH_GCS_PATH`
- `_PIPELINE_TEMPLATE`
- `_TEST_PAYLOAD`
- `_TEST_VERTEX_CMEK_IDENTIFIER` (optional)
- `_TEST_VERTEX_LOCATION`
- `_TEST_VERTEX_NETWORK` (optional)
- `_TEST_VERTEX_PIPELINE_ROOT`
- `_TEST_VERTEX_PROJECT_ID`
- `_TEST_VERTEX_SA_EMAIL`

### On merge to `main` / `master` branch

Set up two triggers for `terraform-apply.yaml`:
  - One for the test environment. Set the substitution value for the variable `_ENV_DIRECTORY` to `envs/test`.
  - One for the prod environment. Set the substitution value for the variable `_ENV_DIRECTORY` to `envs/prod`.
