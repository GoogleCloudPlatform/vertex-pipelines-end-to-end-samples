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

- Suitable GCP environments set up - see the README section on [Deploying Cloud Infrastructure](../README.md#deploying-cloud-infrastructure)
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

When you open the Pull Request, the CI pipeline (`pr-checks.yaml`) should be triggered to run pre-commit checks, unit tests, and compile the training and prediction pipelines. Your E2E checks can also be triggered on the Pull Request (using the `/gcbrun` comment command). Once you are happy with your Pull Request (usual peer review etc), merge it into the main/master branch.

| :bulb: Remember    |
|:-------------------|
| Make sure to update any unit tests and end-to-end tests in line with your changes to the pipelines |

## Creating a release

To compile and publish your ML pipelines into your test and prod environments, you will need to [create a release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository#creating-a-release).

When the new tag is created, the `release.yaml` pipeline should be triggered. It will compile both the training and prediction pipelines, then copy the ML pipelines and their [assets](../README.md#assets) to the Cloud Storage locations specified in your [CI/CD setup](../cloudbuild/README.md) under a folder with the name of your git tag.

#### Example

- You are using the `xgboost` template
- You create a release from the main/master branch and use the git tag `v1.2`
- You have set up the following Cloud Build variables / substitutions for the `release.yaml` CI/CD pipeline
  - `_PIPELINE_PUBLISH_GCS_PATHS` = `gs://<Project ID of dev project>-pl-assets gs://<Project ID of test project>-pl-assets gs://<Project ID of prod project>-pl-assets`

Assuming your end-to-end tests pass, your compiled training pipeline will be published to:
- `gs://<Project ID of dev project>-pl-assets/v1.2/training/training.json`
- `gs://<Project ID of test project>-pl-assets/v1.2/training/training.json`
- `gs://<Project ID of prod project>-pl-assets/v1.2/training/training.json`

The contents of your assets folder for your training pipeline will be published to:
- `gs://<Project ID of dev project>-pl-assets/v1.2/training/assets/`
- `gs://<Project ID of test project>-pl-assets/v1.2/training/assets/`
- `gs://<Project ID of prod project>-pl-assets/v1.2/training/assets/`

Similarly, your compiled prediction pipeline will be published in this location:
- `gs://<Project ID of dev project>-pl-assets/v1.2/prediction/prediction.json`
- `gs://<Project ID of test project>-pl-assets/v1.2/prediction/prediction.json`
- `gs://<Project ID of prod project>-pl-assets/v1.2/prediction/prediction.json`

The contents of your assets folder for your prediction pipeline will be published in this location:
- `gs://<Project ID of dev project>-pl-assets/v1.2/prediction/assets/`
- `gs://<Project ID of test project>-pl-assets/v1.2/prediction/assets/`
- `gs://<Project ID of prod project>-pl-assets/v1.2/prediction/assets/`

| :exclamation: IMPORTANT    |
|:---------------------------|
| Before your E2E tests can run correctly, you need to make sure that the parameters have been set up correctly for the cloud environment in the relevant pipeline definition files (`pipeline.py`). These can inherit from environment variables set in `env.sh` (for triggering ad hoc) or in your Cloud Build trigger setup (for triggering through CI/CD) |

## Deploying a release to the test environment

Now that you have created a release, and the compiled pipelines (and their `assets` files) have been copied to the test and prod environments, you can now schedule your pipelines to run in those environments.

Of course, we will begin by scheduling the pipelines to run in the test environment.

Create a new branch off the main/master branch e.g. `git checkout -b test-env-scheduling`

1. Copy the file `terraform/modules/scheduled_pipelines/scheduled_jobs.auto.tfvars.example` to `terraform/envs/test/scheduled_jobs.auto.tfvars`
1. In this file you will see the variable `cloud_schedulers_config`. Here we pass in a map of all the Cloud Scheduler jobs that we want to deploy. Continuing with our example earlier, the code below shows how we can schedule the training pipeline to run on the first of every month, and the prediction pipeline will run every night:

```
cloud_schedulers_config = {
  # Uncomment and amend as required

  xgboost_training = {
    name         = "xgboost-training-pipeline-trigger"
    description  = "Trigger my XGBoost training pipeline in Vertex"
    schedule     = "0 0 1 * *"
    time_zone    = "UTC"
    template_path = "gs://<Project ID of test project>-pl-assets/v1.2/training/training.json"
    enable_caching = null
    pipeline_parameters = {
      project_id = <Project ID of test project>
      project_location = "europe-west2"
      pipeline_files_gcs_path = "gs://<Project ID of test project>-pl-assets/v1.2/training/assets"
      ingestion_project_id = <Project ID of test project>
      model_name = "xgboost-with-preprocessing"
      model_label = "label_name"
      tfdv_schema_filename = "tfdv_schema_training.pbtxt"
      tfdv_train_stats_path = "gs://<Project ID of test project>-pl-root/train_stats/train.stats"
      dataset_id = "preprocessing"
      dataset_location = "europe-west2"
      ingestion_dataset_id = "chicago_taxi_trips"
      timestamp = "2022-12-01 00:00:00"
    },
  },

    xgboost_prediction = {
    name         = "xgboost-prediction-pipeline-trigger"
    description  = "Trigger my XGBoost prediction pipeline in Vertex"
    schedule     = "0 0 * * *"
    time_zone    = "UTC"
    template_path = "gs://<Project ID of test project>-pl-assets/v1.2/prediction/prediction.json"
    enable_caching = null
    pipeline_parameters = {
      project_id = <Project ID of test project>
      project_location = "europe-west2"
      pipeline_files_gcs_path = "gs://<Project ID of test project>-pl-assets/v1.2/prediction/assets"
      ingestion_project_id = <Project ID of test project>
      model_name = "xgboost-with-preprocessing"
      model_label = "label_name"
      tfdv_schema_filename = "tfdv_schema_prediction.pbtxt"
      tfdv_train_stats_path = "gs://<Project ID of test project>-pl-root/train_stats/train.stats"
      dataset_id = "preprocessing"
      dataset_location = "europe-west2"
      ingestion_dataset_id = "chicago_taxi_trips"
      timestamp = "2022-12-01 00:00:00"
      batch_prediction_machine_type = "n1-standard-4"
      batch_prediction_min_replicas = 3
      batch_prediction_max_replicas = 5
    },
  },

}
```

4. Commit these change to your branch, and push the branch to GitHub
5. Open a Pull Request from this branch to the main/master branch. As part of the CI checks (in Cloud Build), you should see a Terraform plan that describes the changes you have made to the Terraform config
6. Merge the PR to deploy the Cloud Scheduler jobs

## Deploying a release to the production environment

Once you are happy with how `v1.2` is working in the test environment, you can follow the same process for the prod environment (using `terraform/envs/prod`, swapping the necessary values out for the different environment e.g. bucket names).
