# Automated testing for Vertex Pipelines E2E samples

This document details the steps required to set up automated testing with Cloud Build for the [E2E samples repo](https://github.com/GoogleCloudPlatform/vertex-pipelines-end-to-end-samples) (rather than setting up automated testing for your own repo derived from it). It is focused on the Vertex Pipelines components and pipelines themselves, not on the other elements of the codebase such as infrastructure setup.

This guide assumes that you are working in a brand-new Google Cloud project, and that you have Owner permission for this project.

Before you run the below commands, set the environment variables `GCP_PROJECT_ID` and `GCP_REGION` as follows:

```
export GCP_PROJECT_ID=my-gcp-project
export GCP_REGION=us-central1
```

## Core infrastructure

### Google Cloud APIs

The following APIs need to be enabled in the Google Cloud project:

- Vertex AI
- Artifact Registry
- BigQuery
- BigQuery Transfer
- Cloud Build
- Dataflow
- IAM
- Monitoring
- Secret Manager
- Storage

Use this `gcloud` command to do so:

```
gcloud services enable \
aiplatform.googleapis.com \
artifactregistry.googleapis.com \
bigquery.googleapis.com \
bigquerydatatransfer.googleapis.com \
cloudbuild.googleapis.com \
dataflow.googleapis.com \
iam.googleapis.com \
monitoring.googleapis.com \
secretmanager.googleapis.com \
storage-api.googleapis.com \
storage-component.googleapis.com \
storage.googleapis.com \
--project $GCP_PROJECT_ID
```

### Google Cloud Storage buckets

Two buckets will need to be created - one for publishing the compiled JSON pipelines (and any other files required for running the pipelines), and one for the pipeline root.

```
gsutil mb -l ${GCP_REGION} -p ${GCP_PROJECT_ID} gs://${GCP_PROJECT_ID}-pl-root
gsutil mb -l ${GCP_REGION} -p ${GCP_PROJECT_ID} gs://${GCP_PROJECT_ID}-assets 
```

### BigQuery 

Create a new BigQuery dataset for the Chicago Taxi data:

```
bq --location=${GCP_REGION} mk --dataset "${GCP_PROJECT_ID}:chicago_taxi_trips"
```

Create a new BigQuery dataset for data processing during the pipelines:

```
bq --location=${GCP_REGION} mk --dataset "${GCP_PROJECT_ID}:preprocessing"
```

Set up a BigQuery transfer job to mirror the Chicago Taxi dataset to your project

```
bq mk --transfer_config \
  --project_id=${GCP_PROJECT_ID} \
  --data_source="cross_region_copy" \
  --target_dataset="chicago_taxi_trips" \
  --display_name="Chicago taxi trip mirror" \
  --params='{"source_dataset_id":"'"chicago_taxi_trips"'","source_project_id":"'"bigquery-public-data"'"}'
```

### Service Accounts

Two service accounts are required

- One for running Cloud Build jobs
- One for running Vertex Pipelines

Run the commands below

```
gcloud iam service-accounts create cloud-build \
--description="Service account for running Cloud Build" \
--display-name="Custom Cloud Build SA" \
--project=${GCP_PROJECT_ID}

gcloud iam service-accounts create vertex-pipelines \
--description="Service account for running Vertex Pipelines" \
--display-name="Custom Vertex Pipelines SA" \
--project=${GCP_PROJECT_ID}
```

### IAM permissions

The service account we have created for Cloud Build requires the following project roles:

- roles/logging.logWriter
- roles/storage.admin
- roles/aiplatform.user

```
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID --member="serviceAccount:cloud-build@${GCP_PROJECT_ID}.iam.gserviceaccount.com" --role="roles/logging.logWriter" --condition=None
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID --member="serviceAccount:cloud-build@${GCP_PROJECT_ID}.iam.gserviceaccount.com" --role="roles/storage.admin" --condition=None
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID --member="serviceAccount:cloud-build@${GCP_PROJECT_ID}.iam.gserviceaccount.com" --role="roles/aiplatform.user" --condition=None
```

It also requires the "Service Account User" role for the Vertex Pipelines service account ([docs here](https://cloud.google.com/iam/docs/impersonating-service-accounts#impersonate-sa-level)):

```
gcloud iam service-accounts add-iam-policy-binding vertex-pipelines@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
--member="serviceAccount:cloud-build@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
--role="roles/iam.serviceAccountUser" \
--project=${GCP_PROJECT_ID}
```

The Vertex Pipelines service account requires the following project roles:

- roles/aiplatform.user
- roles/bigquery.dataEditor
- roles/bigquery.jobUser

```
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID --member="serviceAccount:vertex-pipelines@${GCP_PROJECT_ID}.iam.gserviceaccount.com" --role="roles/aiplatform.user" --condition=None
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID --member="serviceAccount:vertex-pipelines@${GCP_PROJECT_ID}.iam.gserviceaccount.com" --role="roles/bigquery.dataEditor" --condition=None
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID --member="serviceAccount:vertex-pipelines@${GCP_PROJECT_ID}.iam.gserviceaccount.com" --role="roles/bigquery.jobUser" --condition=None
```

The Vertex Pipelines service account requires read access to the assets bucket, read/write access to the pipeline root bucket, and access to list both buckets:

```
gsutil iam ch serviceAccount:vertex-pipelines@${GCP_PROJECT_ID}.iam.gserviceaccount.com:objectViewer gs://${GCP_PROJECT_ID}-assets

gsutil iam ch serviceAccount:vertex-pipelines@${GCP_PROJECT_ID}.iam.gserviceaccount.com:objectAdmin gs://${GCP_PROJECT_ID}-pl-root

gsutil iam ch serviceAccount:vertex-pipelines@${GCP_PROJECT_ID}.iam.gserviceaccount.com:legacyBucketReader gs://${GCP_PROJECT_ID}-assets

gsutil iam ch serviceAccount:vertex-pipelines@${GCP_PROJECT_ID}.iam.gserviceaccount.com:legacyBucketReader gs://${GCP_PROJECT_ID}-pl-root
```

## Cloud Build setup

### Connect the GitHub repository to Cloud Build

Follow the [Google Cloud documentation](https://cloud.google.com/build/docs/automating-builds/github/connect-repo-github?generation=2nd-gen) to connect the GitHub repository to Cloud Build.

### Set up Cloud Build Triggers

There are five Cloud Build triggers to set up.

1. `pr-checks.yaml` (tensorflow)
2. `pr-checks.yaml` (xgboost)
3. `trigger-tests.yaml` 
4. `e2e-test.yaml` (tensorflow)
5. `e2e-test.yaml` (xgboost)

For each of the above, create a Cloud Build trigger with the following settings:

- Each one should be triggered on Pull Request to the `main` branch
- Enable comment control (select `Required` under `Comment Control`)
- Service account email: `cloud-build@<PROJECT ID>.iam.gserviceaccount.com`
- Configuration -> Type: `Cloud Build configuration file (yaml or json)`
- Configuration -> Location: Repository
- Cloud Build configuration file location: `cloudbuild/pr-checks.yaml` / `cloudbuild/trigger-tests.yaml` / `cloudbuild/e2e-test.yaml`
- Substitution variables - per table below

|  Cloud Build Trigger          |  Substitution variables             |
|-------------------------------|-------------------------------------|
| `pr-checks.yaml` (tensorflow) |  _PIPELINE_TEMPLATE = `tensorflow`  |
| `pr-checks.yaml` (xgboost)    |  _PIPELINE_TEMPLATE = `xgboost`     |
| `trigger-tests.yaml`          |                                     |
| `e2e-test.yaml` (tensorflow)  |  _PIPELINE_TEMPLATE = `tensorflow`<br>_PIPELINE_PUBLISH_GCS_PATH = `gs://<GCP PROJECT ID>-assets/e2e-test-tensorflow`<br>_TEST_ENABLE_PIPELINE_CACHING = `False`<br>_TEST_TRAIN_STATS_GCS_PATH = `gs://<GCP PROJECT ID>-pl-root/e2e-test-tensorflow/train-stats/train.stats`<br>_TEST_VERTEX_LOCATION = `<GCP REGION (same as buckets etc above)>`<br>_TEST_VERTEX_PIPELINE_ROOT = `gs://<GCP PROJECT ID>-pl-root`<br>_TEST_VERTEX_PROJECT_ID = `<GCP PROJECT ID>`<br>_TEST_VERTEX_SA_EMAIL = `vertex-pipelines@<GCP PROJECT ID>.iam.gserviceaccount.com`  |
| `e2e-test.yaml` (xgboost)  |  _PIPELINE_TEMPLATE = `xgboost`<br>_PIPELINE_PUBLISH_GCS_PATH = `gs://<GCP PROJECT ID>-assets/e2e-test-xgboost`<br>_TEST_ENABLE_PIPELINE_CACHING = `False`<br>_TEST_TRAIN_STATS_GCS_PATH = `gs://<GCP PROJECT ID>-pl-root/e2e-test-xgboost/train-stats/train.stats`<br>_TEST_VERTEX_LOCATION = `<GCP REGION (same as buckets etc above)>`<br>_TEST_VERTEX_PIPELINE_ROOT = `gs://<GCP PROJECT ID>-pl-root`<br>_TEST_VERTEX_PROJECT_ID = `<GCP PROJECT ID>`<br>_TEST_VERTEX_SA_EMAIL = `vertex-pipelines@<GCP PROJECT ID>.iam.gserviceaccount.com`  |
