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

# Running ML pipelines in production

This document describes the full process from making a change to your pipeline code, all the way through to having the code running in production.

## Pre-requisites

- Suitable GCP environments set up - see the README section on [Cloud Architecture](../README.md#cloud-architecture)
- This repo forked / used as a template for a new GitHub repo
- CI/CD set up - see the instructions [here](cloudbuild/README.md)
- Access set up for the BigQuery datasets used in the example pipelines
- Git repo cloned locally (or in a notebook environment) and local setup complete - see [here](../README.md#local-setup)

## Making your changes to the pipelines

1. Create a feature branch off the main/master branch: `git checkout -b my-feature-branch`
1. Make changes to your pipeline code locally (see main README and [USAGE.md](../USAGE.md) for more details)
1. Commit these changes to your feature branch
1. Push your feature branch to GitHub
1. Open a Pull Request (PR) from your feature branch to the main/master branch

When you open the Pull Request, the CI pipeline (`pr-checks.yaml`) should be triggered to run pre-commit checks, unit tests, and compile the training and prediction pipelines. Once you are happy with your Pull Request (usual peer review etc), merge it into the main/master branch.

| :bulb: Remember    |
|:-------------------|
| Make sure to update any unit tests and end-to-end tests in line with your changes to the pipelines |

## Creating a release

To compile and publish your ML pipelines into your test and prod environments, you will need to [create a release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository#creating-a-release).

When the new tag is created, the `release.yaml` pipeline should be triggered. It will compile both the training and prediction pipelines, and run the end-to-end tests on each in turn in your test environment. Assuming they complete successfully, the ML pipelines and their [assets](../README.md#assets) will be copied to the Cloud Storage locations specified in your [CI/CD setup](../cloudbuild/README.md#cicd-setup) under a folder with the name of your git tag.

#### Example

- You are using the `xgboost` template
- You create a release from the main/master branch and use the git tag `v1.2`
- You have set up the following Cloud Build variables / substitutions for the `release.yaml` CI/CD pipeline
  - `_PIPELINE_PUBLISH_GCS_PATH` = `gs://my-cicd-env-bucket/pipelines`

Assuming your end-to-end tests pass, your compiled training pipeline will be published in this location:
- `gs://my-cicd-env-bucket/pipelines/v1.2/training/training.json`

The contents of your assets folder for your training pipeline will be published in this location:
- `gs://my-cicd-env-bucket/pipelines/v1.2/training/assets/`

Similarly, your compiled prediction pipeline will be published in this location:
- `gs://my-cicd-env-bucket/pipelines/v1.2/prediction/prediction.json`

The contents of your assets folder for your prediction pipeline will be published in this location:
- `gs://my-cicd-env-bucket/pipelines/v1.2/prediction/assets/`

| :exclamation: IMPORTANT    |
|:---------------------------|
| Before your E2E tests can run correctly, you need to make sure that the parameters have been set up correctly for the test environment in the test payload file `pipelines/<template>/<training\|prediction>/payloads/test.json` |

## Deploying a release to the test environment

Now that you have created a release, and the compiled pipelines (and their `assets` files) have been copied to the test and prod environments, you can now schedule your pipelines to run in those environments.

Of course, we will begin by scheduling the pipelines to run in the test environment.

Create a new branch off the main/master branch e.g. `git checkout -b test-env-scheduling`

We need to set up the Terraform configuration for the test environment:

1. In `envs/test/main.tf`, set up the backend configuration of Terraform, so that the Terraform state is stored somewhere in GCS (note that this step is only required the first time you set this up).

| :boom: BE CAREFUL    |
|:---------------------|
| Make sure that the Terraform state for the test environment (in `envs/test`) and the prod environment (in `envs/prod`) are not set to reside in the same GCS location! |

2. Set up the following Terraform variables in `envs/test/variables.auto.tfvars`:
  - `project_id`
  - `pubsub_topic_name`
3. For the variable `cloud_schedulers_config`, we pass in a map of all the Cloud Scheduler jobs that we want to deploy. Continuing with our example earlier, the code below shows how we can schedule the training pipeline to run on the first of every month, and the prediction pipeline will run every night:

```
cloud_schedulers_config = {
  training = {
    name        = "training-pipeline-trigger",
    region      = "europe-west4", # Must be the same as the App Engine region
    description = "Trigger my training pipeline in Vertex",
    schedule    = "0 0 1 * *", # training pipeline runs on 1st of each month at midnight
    time_zone   = "UTC",
    # Relative path to payload JSON file for this environment
    payload_file = "../../pipelines/xgboost/training/payloads/test.json",
  },
  prediction = {
    name        = "prediction-pipeline-trigger",
    region      = "europe-west4", # Must be the same as the App Engine region
    description = "Trigger my prediction pipeline in Vertex",
    schedule    = "0 2 * * *", # 2AM each day
    time_zone   = "UTC",
    # Relative path to payload JSON file for this environment
    payload_file = "../../pipelines/xgboost/prediction/payloads/test.json",
  },
}
```

4. We need to update those payload files (`test.json`) to point to our `v1.2` version of the pipelines.

Update these parameters in `pipelines/xgboost/training/test.json`:

- `"template_path": "gs://my-cicd-env-bucket/pipelines/v1.2/training/training.json"`
- `"pipeline_files_gcs_path": "gs://my-cicd-env-bucket/pipelines/v1.2"`

Update these parameters in `pipelines/xgboost/prediction/test.json`:

- `"template_path": "gs://my-cicd-env-bucket/pipelines/v1.2/prediction/prediction.json"`
- `"pipeline_files_gcs_path": "gs://my-cicd-env-bucket/pipelines/v1.2"`

5. Commit these change to your branch, and push the branch to GitHub
6. Open a Pull Request from this branch to the main/master branch. As part of the CI checks (in Cloud Build), you should see a Terraform plan that describes the changes you have made to the Terraform config
7. Merge the PR to deploy the Cloud Scheduler jobs

## Deploying a release to the production environment

Once you are happy with how `v1.2` is working in the test environment, you can follow the same process for the prod environment (using `envs/prod` and `prod.json`, swapping the necessary values out for the different environment e.g. bucket names).
