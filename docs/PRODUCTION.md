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

- Suitable GCP environments set up - see the README section on [Deploying Cloud Infrastructure](/README.md#deploying-cloud-infrastructure)
- This repo forked / used as a template for a new GitHub repo
- CI/CD set up - see the instructions [here](cloudbuild/README.md)
- Access set up for the BigQuery datasets used in the example pipelines
- Git repo cloned locally (or in a notebook environment) and local setup complete - see [here](/README.md#local-setup)

## Making your changes to the pipelines

1. Create a feature branch off the main/master branch: `git checkout -b my-feature-branch`
1. Make changes to your pipeline code locally (e.g. `pipelines/src/pipelines/training.py`)
1. Commit these changes to your feature branch
1. Push your feature branch to GitHub
1. Open a Pull Request (PR) from your feature branch to the main/master branch

When you open the Pull Request, the CI pipeline (`pr-checks.yaml`) should be triggered to run pre-commit checks, unit tests, and compile the training and prediction pipelines. Your E2E checks can also be triggered on the Pull Request (using the `/gcbrun` comment command). Once you are happy with your Pull Request (usual peer review etc), merge it into the main/master branch.

| :bulb: Remember    |
|:-------------------|
| Make sure to update any unit tests in line with your changes to the pipelines |

| :exclamation: IMPORTANT    |
|:---------------------------|
| Before your E2E tests can run correctly, you need to make sure that the parameters have been set up correctly for the cloud environment in the relevant pipeline definition files (`pipeline.py`). These can inherit from environment variables set in `env.sh` (for triggering ad hoc) or in your Cloud Build trigger setup (for triggering through CI/CD) |

## Creating a release

To compile and publish your ML pipelines into your test and prod environments, you will need to [create a release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository#creating-a-release).

When the new tag is created, the `release.yaml` pipeline should be triggered. It will build and push the training and serving container images, compile the training and prediction pipelines, then upload the compiled ML pipelines to Artifact Registry in each environment (dev/test/prod).

#### Example

- You have set up the following Cloud Build variables / substitutions for the `release.yaml` CI/CD pipeline
  - `_PIPELINE_PUBLISH_AR_PATHS` = `https://<GCP region>-kfp.pkg.dev/<Project ID of dev project>/vertex-pipelines https://<GCP region>-kfp.pkg.dev/<Project ID of test project>/vertex-pipelines https://<GCP region>-kfp.pkg.dev/<Project ID of prod project>/vertex-pipelines`
- You create a release from the main/master branch and use the git tag `v1.2`

Your compiled training pipeline will be published to:
- `https://<GCP region>-kfp.pkg.dev/<Project ID of dev project>/vertex-pipelines/xgboost-train-pipeline/v1.2`
- `https://<GCP region>-kfp.pkg.dev/<Project ID of test project>/vertex-pipelines/xgboost-train-pipeline/v1.2`
- `https://<GCP region>-kfp.pkg.dev/<Project ID of prod project>/vertex-pipelines/xgboost-train-pipeline/v1.2`

Similarly, your compiled prediction pipeline will be published in these locations:
- `https://<GCP region>-kfp.pkg.dev/<Project ID of dev project>/vertex-pipelines/xgboost-prediction-pipeline/v1.2`
- `https://<GCP region>-kfp.pkg.dev/<Project ID of test project>/vertex-pipelines/xgboost-prediction-pipeline/v1.2`
- `https://<GCP region>-kfp.pkg.dev/<Project ID of prod project>/vertex-pipelines/xgboost-prediction-pipeline/v1.2`

## Deploying a release to the test environment

Now that you have created a release, and the compiled pipelines have been copied to the test and prod environments, you can now schedule your pipelines to run in those environments.

Of course, we will begin by scheduling the pipelines to run in the test environment.

Create a new branch off the main/master branch e.g. `git checkout -b test-env-scheduling`

1. Copy the file `terraform/modules/scheduled_pipelines/scheduled_jobs.auto.tfvars.example` to `terraform/envs/test/scheduled_jobs.auto.tfvars`
1. In this file you will see the variable `cloud_schedulers_config`. Here we pass in a map of all the Cloud Scheduler jobs that we want to deploy. Continuing with our example earlier, the code below shows how we can schedule the training pipeline to run on the first of every month, and the prediction pipeline will run every night:

```
cloud_schedulers_config = {

  training = {
    description  = "Trigger training pipeline in Vertex AI"
    schedule     = "0 0 1 * *"
    time_zone    = "UTC"
    template_path = "https://<GCP region>-kfp.pkg.dev/<Project ID of test project>/vertex-pipelines/xgboost-train-pipeline/v1.2"
    enable_caching = null
    pipeline_parameters = {
      // Add pipeline parameters which are expected by your pipeline here e.g.
      // project = "my-project-id"
    },
  },

  prediction = {
    description  = "Trigger prediction pipeline in Vertex AI"
    schedule     = "0 0 * * *"
    time_zone    = "UTC"
    template_path = "https://<GCP region>-kfp.pkg.dev/<Project ID of test project>/vertex-pipelines/xgboost-prediction-pipeline/v1.2"
    enable_caching = null
    pipeline_parameters = {
      // Add pipeline parameters which are expected by your pipeline here e.g.
      // project = "my-project-id"
    },
  },

}
```

4. Commit these change to your branch, and push the branch to GitHub
5. Open a Pull Request from this branch to the main/master branch. As part of the CI checks (in Cloud Build), you should see a Terraform plan that describes the changes you have made to the Terraform config
6. Merge the PR to deploy the Cloud Scheduler jobs

## Deploying a release to the production environment

Once you are happy with how `v1.2` is working in the test environment, you can follow the same process for the prod environment (using `terraform/envs/prod`, swapping the necessary values out for the different environment e.g. Artifact Registry names).
