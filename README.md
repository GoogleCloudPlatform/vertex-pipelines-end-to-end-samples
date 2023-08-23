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

# Vertex Pipelines End-to-end Samples

_AKA "Vertex AI Turbo Templates"_

## Introduction

This repository provides a reference implementation of [Vertex Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/) for creating a production-ready MLOps solution on Google Cloud.
You can take this repository as a starting point you own ML use cases. The implementation includes:

* Infrastructure-as-Code using Terraform for a typical dev/test/prod setup of Vertex AI and other relevant services
* ML training and batch prediction pipelines using the Kubeflow Pipelines SDK for an example use case (using the [Chicago Taxi Trips Dataset](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=chicago_taxi_trips&page=dataset))
* Reusable KFP components that can be used in ML pipelines
* CI/CD using Google Cloud Build for linting, testing, and deploying ML pipelines
* Developer scripts (Makefile, Python scripts etc)

## Cloud Architecture

The diagram below shows the cloud architecture for this repository.

![Cloud Architecture diagram](/docs/images/architecture.png)

There are four different Google Cloud projects in use

* `dev` - a shared sandbox environment for use during development
* `test` - environment for testing new changes before they are promoted to production. This environment should be treated as much as possible like a production environment.
* `prod` - production environment
* `admin` - separate Google Cloud project for setting up CI/CD in Cloud Build (since the CI/CD pipelines operate across the different environments)

Vertex Pipelines are scheduled using Google Cloud Scheduler. Cloud Scheduler emits a Pub/Sub message that triggers a Cloud Function, which in turn triggers the Vertex Pipeline to run. _In future, this will be replaced with the Vertex Pipelines Scheduler (once there is a Terraform resource for it)._

## Infrastructure

The cloud infrastructure is managed using Terraform and is defined in the [`terraform`](terraform) directory. There are three Terraform modules defined in [`terraform/modules`](terraform/modules):

- `cloudfunction` - deploys a (Pub/Sub-triggered) Cloud Function from local source code
- `scheduled_pipelines` - deploys Cloud Scheduler jobs that will trigger Vertex Pipeline runs (via the above Cloud Function)
- `vertex_deployment` - deploys Cloud infrastructure required for running Vertex Pipelines, including enabling APIs, creating buckets, Artifact Registry repos, service accounts, and IAM permissions.

There is a Terraform configuration for each environment (dev/test/prod) under [`terraform/envs`](terraform/envs/).

How to deploy this infrastructure is covered in a [later section](#deploying-infrastructure).

## Developer setup

### Prerequisites

- [Pyenv](https://github.com/pyenv/pyenv#installation) for managing Python versions
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/quickstart)
- Make

### Local setup

1. Clone the repository locally (or create a new repo from this template)
1. Install the correct Python version: `pyenv install`
1. Install poetry - follow the instructions in the [poetry documentation](https://python-poetry.org/docs/#installation)
1. Configure poetry to use the Python version from pyenv: `poetry config virtualenvs.prefer-active-python true`
1. Install poetry dependencies for ML pipelines: `make install`
1. Install pre-commit hooks: `cd pipelines && poetry run pre-commit install`
1. Copy `env.sh.example` to `env.sh`, and update the environment variables in `env.sh` for your dev environment (particularly `VERTEX_PROJECT_ID`, `VERTEX_LOCATION` and `RESOURCE_SUFFIX`)
1. Authenticate to Google Cloud
    1. `gcloud auth login`
    1. `gcloud auth application-default login`

### Deploying infrastructure

You will need four Google Cloud projects:

- dev
- test
- prod
- admin

The Cloud Build pipelines will run in the _admin_ project, and deploy resources into the dev/test/prod projects.

Before your CI/CD pipelines can deploy the infrastructure, you will need to set up a Terraform state bucket for each environment:

```bash
gsutil mb -l <GCP region e.g. europe-west2> -p <DEV PROJECT ID> --pap=enforced gs://<DEV PROJECT ID>-tfstate && gsutil ubla set on gs://<DEV PROJECT ID>-tfstate

gsutil mb -l <GCP region e.g. europe-west2> -p <TEST PROJECT ID> --pap=enforced gs://<TEST PROJECT ID>-tfstate && gsutil ubla set on gs://<TEST PROJECT ID>-tfstate

gsutil mb -l <GCP region e.g. europe-west2> -p <PROD PROJECT ID> --pap=enforced gs://<PROD PROJECT ID>-tfstate && gsutil ubla set on gs://<PROD PROJECT ID>-tfstate
```

You will also need to manually enable the Cloud Resource Manager and Service Usage APs for your _admin_ project:

```bash
gcloud services enable cloudresourcemanager.googleapis.com --project=<ADMIN PROJECT ID>
gcloud services enable serviceusage.googleapis.com --project=<ADMIN PROJECT ID>
```

Install Terraform on your local machine. We recommend using [`tfswitch`](https://tfswitch.warrensbox.com/) to automatically choose and download an appropriate version for you (run `tfswitch` from the [`terraform/envs/dev`](terraform/envs/dev/) directory).

Now you can deploy the infrastructure using Terraform:

```bash
make deploy env=dev VERTEX_PROJECT_ID=<DEV PROJECT ID>
make deploy env=test VERTEX_PROJECT_ID=<TEST PROJECT ID>
make deploy env=prod VERTEX_PROJECT_ID=<PROD PROJECT ID>
```

#### Optional - Tearing down infrastructure

To tear down the infrastructure you have created with Terraform, run these commands:

```bash
make undeploy env=dev VERTEX_PROJECT_ID=<DEV PROJECT ID>
make undeploy env=test VERTEX_PROJECT_ID=<TEST PROJECT ID>
make undeploy env=prod VERTEX_PROJECT_ID=<PROD PROJECT ID>
```

### Example ML pipelines

This repository contains example ML training and prediction pipelines for scikit-learn/XGBoost using the popular [Chicago Taxi Dataset](https://console.cloud.google.com/marketplace/details/city-of-chicago-public-data/chicago-taxi-trips). The details of these can be found in the [separate README](pipelines/README.md).

#### Pre-requisites

Before you can run these example pipelines successfully there are a few additional things you will need to deploy into each environment (they have not been included in the Terraform code as they are specific to these Chicago Taxi pipelines)

1. Create a new BigQuery dataset for the Chicago Taxi data:

```
bq --location=${VERTEX_LOCATION} mk --dataset "${VERTEX_PROJECT_ID}:chicago_taxi_trips"
```

2. Create a new BigQuery dataset for data processing during the pipelines:

```
bq --location=${VERTEX_LOCATION} mk --dataset "${VERTEX_PROJECT_ID}:preprocessing"
```

3. Set up a BigQuery transfer job to mirror the Chicago Taxi dataset to your project

```
bq mk --transfer_config \
  --project_id=${VERTEX_PROJECT_ID} \
  --data_source="cross_region_copy" \
  --target_dataset="chicago_taxi_trips" \
  --display_name="Chicago taxi trip mirror" \
  --params='{"source_dataset_id":"'"chicago_taxi_trips"'","source_project_id":"'"bigquery-public-data"'"}'
```

### Building the container images

The [model/](/model/) directory contains the code for custom training and serving container images, including the model training script at [model/training/train.py](model/training/train.py). You can modify this to suit your own use case.

Build the training and serving container images and push them to Artifact Registry with:

```bash
make build
```

Optionally specify the `target` variable to only build one of the images. For example, to build only the serving image:

```bash
make build target=serving
```

### Running Pipelines

You can run the training pipeline (for example) with:

```bash
make run pipeline=training
```

This will execute the pipeline using the chosen template on Vertex AI, namely it will:

1. Compile the pipeline using the Kubeflow Pipelines SDK
1. Trigger the pipeline with the help of `pipelines/trigger/main.py`

#### Pipeline input parameters

The ML pipelines have input parameters. As you can see in the pipeline definition files (`pipelines/src/pipelines/<training|prediction>/pipeline.py`), they have default values, and some of these default values are derived from environment variables (which in turn are defined in `env.sh`).

When triggering ad hoc runs in your dev/sandbox environment, or when running the E2E tests in CI, these default values are used. For the test and production deployments, the pipeline parameters are defined in the Terraform code for the Cloud Scheduler jobs (`terraform/envs/<dev|test|prod>/scheduled_jobs.auto.tfvars`) - see the section on [Scheduling pipelines](#scheduling-pipelines).

## Testing

Unit tests and end-to-end (E2E) pipeline tests are performed using [pytest](https://docs.pytest.org). 
The unit tests for custom KFP components are run on each pull request, as well as the E2E tests. To run them on your local machine:

```
make test
```

Alternatively, only test one of the component groups by running:
```
make test GROUP=vertex-components
```

To run end-to-end tests of a single pipeline, you can use:

```
make e2e-tests pipeline=<training|prediction>
```

There are also unit tests for the utility scripts in [pipelines/src/pipelines/utils](/pipelines/src/pipelines/utils/). To run them on your local machine:

```
make test
```

## Customize pipelines

### Adding a new pipeline

This repository contains a training and a (batch) prediction pipeline. To add another ML pipeline (e.g. for continuous evaluation), create a new directory under the `pipelines/src/pipelines` directory. Within your new pipeline folder, create a `pipeline.py` file - this is where you should provide your pipeline definition using the KFP DSL (in a function named `pipeline`).

Alternatively, you can just copy and paste the `training` or `prediction` directory.

See below for an example folder structure:

```
vertex-pipelines-end-to-end-samples
|
├── pipelines
│   ├── src
│   │   ├── pipelines
│   │   │   ├── new_pipeline
│   │   │   │   ├── pipeline.py
│   │   │   │   └── queries
│   │   │   │       └── my_query.sql
```

Make sure that you give the ML pipeline a unique name in the `@pipeline` decorator.

To run your pipeline, use `make run` as before:

```bash
make run pipeline=your_new_pipeline
```

You will also need to add an E2E test - copy and paste the `training` or `prediction` example in [pipelines/tests/](/pipelines/tests/).

Some of the scripts e.g. CI/CD pipelines assume only a training and prediction pipeline. You will need to adapt these to add in the compile, run and upload steps for your new pipeline in [cloudbuild/pr-checks.yaml](/cloudbuild/pr-checks.yaml), [cloudbuild/e2e-test.yaml](/cloudbuild/e2e-test.yaml) and [cloudbuild/release.yaml](/cloudbuild/release.yaml).

### Scheduling pipelines

Terraform is used to deploy Cloud Scheduler jobs that trigger the Vertex Pipeline runs. This is done by the CI/CD pipelines (see section below on CI/CD).

To schedule pipelines into an environment, you will need to provide the `cloud_schedulers_config` variable to the Terraform configuration for the relevant environment. You can find an example of this configuration in [`terraform/modules/scheduled_pipelines/scheduled_jobs.auto.tfvars.example`](terraform/modules/scheduled_pipelines/scheduled_jobs.auto.tfvars.example). Copy this example file into the relevant directory for your environment (e.g. `terraform/envs/dev` for the dev environment) and remove the `.example` suffix. Adjust the configuration file as appropriate.

## CI/CD

For details on setting up CI/CD, see the [CI/CD README](/cloudbuild/README.md).

For details on setting up CI/CD for the template codebase itself (instead of for your own ML use case), follow the guide [here](/docs/TESTING_SETUP.md).

## Putting it all together

For a full walkthrough of the journey from changing the ML pipeline code to having it scheduled and running in production, please see the guide [here](docs/PRODUCTION.md).
