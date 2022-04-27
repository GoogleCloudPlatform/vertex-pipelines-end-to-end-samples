# Vertex Pipelines End-to-end Samples

## Introduction

This repository provides a reference implementation of [Vertex Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/) for creating a production-ready MLOps solution on Google Cloud.

### Why does this matter?

It is hard to productionalize data science use cases, especially because the journey from experimentation is lacking standardisation. 
Thus, this project aims at boosting, scalability, productivity and standardisation of data science use cases amongst data science teams.
As a result, this will free up time for data scientists so that they can focus on data science with minimal engineering overhead.

This project bundles reusable code and provides the creation of a MLOps platform via an template-driven approach allowing to:

- **Create a new use case from a template.** Create a new ML training pipeline and batch prediction pipeline based on a template. 
- **Execute a one-off pipeline run in a sandbox environment.** Try out a pipeline during the development cycle in a sandbox (development) environment.
- **Deploy a pipeline to a production environment.** Deploy a new or updated pipeline to a production environment allowing for orchestration, schedules and triggers.
- **Publish a new template.** Customize or extend the existing templates to create a new pipeline template that can be used by the data scientists on the team to support new use cases.

As such, this project includes the infrastructure on Google Cloud, a CI/CD integration and existing templates to support training and prediction pipelines for common ML frameworks such as TensorFlow and XGBoost.
To showcase the pipelines in action, the [Public Chicago Taxi Trips Dataset](https://console.cloud.google.com/bigquery?p=bigquery-public-data&d=chicago_taxi_trips&page=dataset) is used to predict the total fare of a taxi trip in Chicago.

### Cloud Architecture

Vertex AI Pipelines is a serverless orchestrator for running ML pipelines, using either the KFP SDK or TFX. However, unlike Kubeflow Pipelines, it does not have a built-in mechanism for saving Pipelines so that they can be run later, either on a schedule or via an external trigger. Instead, every time you want to run an ML pipeline in Vertex AI, you must make the API call to Vertex AI Pipelines, including the full pipeline definition, and Vertex Pipelines will run the pipeline there and then.

In a production MLOps solution, your ML pipelines need to be repeatable. So, we have created a Cloud Function to trigger the execution of ML pipelines on Vertex AI. This can be done either using a schedule (via Cloud Scheduler), or from an external system using Pub/Sub. We use Cloud Build to compile the pipelines using the KFP SDK, and publish them to a GCS bucket. The Cloud Function retrieves the pipeline definition from the bucket, and triggers an execution of the pipeline in Vertex AI.

See [Infrastructure](terraform/README.md) for an implementation of a GCP deployment in the form of a Terraform module.

![Using a Cloud Function to trigger Vertex Pipelines](docs/images/cf_view.png)

## Getting started

### Prerequisites

- Python 3.7.12
- [Cloud SDK](https://cloud.google.com/sdk/docs/quickstart)
- [pyenv](https://github.com/pyenv/pyenv/wiki#suggested-build-environment)

For Unix users, we recommend the use of `pyenv` to manage the Python version as specifed in `.python-version`. See the [installation instruction](https://github.com/pyenv/pyenv#installation) for setting up `pyenv` on your system.

<details><summary>What if my project is outside of any US region?</summary><p>

Since the Chicago Taxi Trips dataset isn't available outside of the US, 
a one-time manual copy of this dataset to your project location using the [BigQuery Data Transfer Service](https://cloud.google.com/bigquery-transfer/docs/introduction) is needed.

1. Ensure you have the [required permissions](https://cloud.google.com/bigquery-transfer/docs/working-with-transfers#required_permissions_5)
1. Enable BigQuery Data Transfer API enabled in your project `gcloud services enable bigquerydatatransfer.googleapis.com`
1. Run `bash transfer_dataset.sh <project_id> <dataset> <location>`
</p></details>

### Local setup

In the repository, execute:

1. Install Python: `pyenv install`
1. Install pipenv: `pip install pipenv`
1. Install pipenv dependencies: `pipenv install --dev`
1. Install pre-commit hooks: `pipenv run pre-commit install`
1. Copy `env.sh.example` to `env.sh`, and update the environment variables in `env.sh`

### Run pipelines
    
This project supports a no. of pipeline templates (see the [separate README](pipelines/README.md) for the pipelines in detail) which can be invoked by setting the environment variable `PIPELINE_TEMPLATE` and executing the `make`:

| ML Framework | Pipeline | `PIPELINE_TEMPLATE` |
| --- | --- | --- |
| XGBoost | Training | `xgboost` |
| XGBoost | Prediction | `xgboost` |
| TensorFlow | Training | `tensorflow` |
| TensorFlow | Prediction | `tensorflow` |

For example, you can run the XGBoost training pipeline with:

```
make run PIPELINE_TEMPLATE=xgboost pipeline=training
```

Alternatively, add the environment variable `PIPELINE_TEMPLATE=xgboost` and/or `pipeline=training` to `env.sh`, then:

```bash
make run pipeline=<training|prediction>
```

This will execute the pipeline using the chosen template on Vertex AI, namely it will:

1. Compile the pipeline using the Kubeflow Pipelines SDK
1. Copy the `assets` folders to Cloud Storage
1. Trigger the pipeline with the help of `pipelines/trigger/main.py`
    
The trigger mechanism uses a payload to pass static as well as dynamic metadata to a pipeline. 
The next section explain this content and usage of the payload in more detail.

#### Pipeline payload

For each pipeline, there is a JSON file that contains the pipeline parameters (and some other parameters) for the pipeline run in the sandbox/dev environment. 
You can view and modify this file in `./pipelines/$PIPELINE_TEMPLATE/$pipeline/payloads/dev.json`. 
There are also payload files for test and prod environments.

<details><summary>More details about the contents of payload</summary><p>

```json
{
    "attributes": { 
        "enable_caching": "False",
        "template_path": "<local path for the compiled ML pipeline - or for the test/prod environments, GCS location for the compiled ML pipeline to use>"
    },
    "data": {
        "key": "value"
    }
}
```
    
| Payload Field | Purpose | Comments |
| --- | --- | --- |
| `enable_caching` | Control the [caching behaviour in Vertex Pipelines](https://cloud.google.com/vertex-ai/docs/pipelines/configure-caching) | <ul><li>If set to "True", Vertex Pipelines will cache the outputs of any pipeline steps where the component's specification, inputs, output definition, and pipeline name are identical</li><li>If set to "False", Vertex Pipelines will never cache the outputs of any pipeline steps</li><li>If it is not included, Vertex Pipelines will default to caching the outputs of pipeline steps where possible, unless caching is disabled in the pipeline definition</li> |
| `template_path` | Specify where the compiled ML pipeline to run should be stored - either a local path (for development) or a GCS path (for scheduling) |  |
| `data` | Key-value pairs of any additional input parameters for the ML pipeline | The pipeline keys and values differ between pipelines e.g. `"model_name": "my-xgboost-model"`. |
</p>
</details>

### Assets

In each pipeline folder, there is an `assets` directory (`pipelines/<xgboost|tensorflow>/<training|prediction>/assets/`). This can be used for any additional files that may be needed during execution of the pipelines. 
For the example pipelines, it may contain data schemata (for Data Validation) or training scripts. This [notebook](pipelines/schema_creation.ipynb) gives an example on schema generation. 
This directory is rsync'd to Google Cloud Storage when running a pipeline in the sandbox environment or as part of the CD pipeline (see [CI/CD setup](cloudbuild/README.md)).

## Testing

Unit tests and end-to-end (E2E) pipeline tests are performed using [pytest](https://docs.pytest.org). The unit tests for custom KFP components are run on each pull request, and the E2E tests are run on merge to the main branch. To run them on your local machine:

```
make unit-tests
```

and

```
make e2e-tests pipeline=<training|prediction>
```

There are also unit tests for the pipeline triggering code [`pipelines/trigger`](../pipelines/trigger). This is not run as part of a CI/CD pipeline, as we don't expect this to be changed for each use case. To run them on your local machine:

```
make trigger-tests
```

## Customize pipelines

### Start a new project

There are three ways to create a new project from this template as outlined below.

**GitHub UI**

On the repository main page, click on "Use this template". then continue to create a new repository based on the master branch.

![Use template](./docs/images/use_template.png)

**Github CLI**

Create a new git repo, using this directory as a starting point: `gh repo create <repo name> -p <link-to-this-repository>`.

**Git CLI**

Assuming you already have an empty REMOTE repository (i.e. in GitHub), use the following commands:

```bash
git clone <link-to-this-repository>              # clone this repo as a template
git remote rm origin                             # remove upstream origin
git remote add origin <link-to-new-repository>   # add new upstream origin
git push -u origin master                        # push to new upstream repo
```

### Update existing pipelines

See existing [XGBoost](pipelines/xgboost) and [Tensorflow](pipelines/tensorflow) pipelines as part of this template.
Update `PIPELINE_TEMPLATE` to `xgboost` or `tensorflow` in [env.sh](env.sh.example) to specify whether to run the XGBoost pipelines or TensorFlow pipelines. 
Make changes to the ML pipelines and their associated tests.
Refer to the [contribution instructions](CONTRIBUTING.md) for more information on committing changes. 

### Add new pipelines

See [USAGE](USAGE.md) for guidelines on how to add new pipelines (e.g. other than XGBoost and TensorFlow).

### Scheduling pipelines

Terraform is used to deploy Cloud Scheduler jobs that trigger the Vertex Pipeline runs. This is done by the CI/CD pipelines (see section below on CI/CD).

#### Configuring Terraform

The Terraform configuration is provided for two environments under the `envs` directory - `envs/test` and `envs/prod`. Each will need some setup steps for their respective environment:

1. In `main.tf`, you will need to configure the GCS location for the Terraform state. For example, the following configuration will store the Terraform state file under the directory `gs://my-tf-state-bucket/path/to/tfstate`.

```
  backend "gcs" {
    bucket = "my-tfstate-bucket" # Change this
    prefix = "/path/to/tfstate"  # Change this
  }
```

Remember that this configuration must be different for the two environments.

2. In `variables.auto.tfvars`, you need to configure the following variables:
  - `project_id` - the GCP project ID for your Cloud Scheduler jobs.
  - `pubsub_topic_name` - the name of the Pub/Sub topic that the Cloud Scheduler job should publish to. This is the same Pub/Sub topic that your Cloud Function must be subscribed to.
  - `cloud_schedulers_config` - a map of Cloud Scheduler jobs that you want to deploy. An example is given for scheduling a training pipeline.

### CI/CD

There are four CI/CD pipelines located under the [cloudbuild](cloudbuild) directory:

1. `pr-checks.yaml` - runs pre-commit checks and unit tests on the custom KFP components, and checks that the ML pipelines (training and prediction) can compile.
2. `release.yaml` - Compiles the training and prediction pipelines, and copies the compiled pipelines, along with their respective `assets` directories, to Google Cloud Storage in the build / CI/CD environment. The Google Cloud Storage destination is namespaced using the git tag (see below). Following this, the E2E tests are run on the new compiled pipelines. Below is a diagram of how the files are published in each environment:

```
. <-- GCS directory set by _PIPELINE_PUBLISH_GCS_PATH
└── TAG_NAME <-- Git tag used for the release
    ├── prediction
    │   ├── assets
    │   │   └── tfdv_schema_prediction.pbtxt
    │   └── prediction.json   <-- compiled prediction pipeline
    └── training
        ├── assets
        │   └── tfdv_schema_training.pbtxt
        └── training.json   <-- compiled training pipeline
```

3. `terraform-plan.yaml` - Checks the Terraform configuration under `envs/<env>` (i.e. `envs/test` or `envs/prod`), and produces a summary of any proposed changes that will be applied on merge to the main branch. Out of the box, this just includes Cloud Scheduler jobs used to schedule your ML pipelines.
4. `terraform-apply.yaml` - Applies the Terraform configuration under `envs/<env>` (i.e. `envs/test` or `envs/prod`). Out of the box, this just includes Cloud Scheduler jobs used to schedule your ML pipelines.
 

For more details on setting up CI/CD, see the [separate README](cloudbuild/README.md).

For a full walkthrough of the journey from changing the ML pipeline code to having it scheduled and running in production, please see the guide [here](docs/PRODUCTION.md).

### Using Dataflow

The `generate_statistics` pipeline component generates statistics about a given dataset (using the [`generate_statistics_from_csv`](https://www.tensorflow.org/tfx/data_validation/api_docs/python/tfdv/generate_statistics_from_csv) function in the [TensorFlow Data Validation](https://www.tensorflow.org/tfx/guide/tfdv) package) can optionally be run using [DataFlow](https://cloud.google.com/dataflow/) to scale to huge datasets.

For instructions on how to do this, see the [README](pipelines/kfp_components/tfdv/generate_statistics.md) for this component.
