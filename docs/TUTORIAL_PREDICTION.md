# Introduction to E2E Samples of Vertex Pipelines - Prediction Pipeline


## Let's get started!

This guide will show you how to use the template & run an end-to-end Vertex ML Prediction Pipeline using XGBoost.

**Pre-requisites**:

- You have a Google Cloud Platform account and a Google Project
- You have enabled the following API's for the above project
    - Vertex AI
    - Cloud BigQuery
    - Cloud Storage
- You have run the training pipeline from the template previously

**Time to complete**: About 45 minutes

Click the **Start** button to move to the next step.


## Vertex Pipelines End-to-end sample - Prediction Pipeline

It is hard to productionize data science use cases, especially because the journey from experimentation lacks standardisation. 

This GitHub repository bundles reusable code and provides the creation of a MLOps platform via an template-driven approach allowing to:

- **Create a new use case from a template**: Create a new ML training pipeline and batch prediction pipeline based on a template.
- **Deploy a pipeline to a production environment**: Deploy a new or updated pipeline to a production environment allowing for orchestration, schedules and triggers.

As such, this project includes the infrastructure on Google Cloud, a CI/CD integration and existing templates to support training and prediction pipelines for common ML frameworks such as TensorFlow and XGBoost.

TODO: Add reference links


## Setup

TODO: Add project selection dropdown (if feasible)

Execute the following commands:

1. Install Python (if not installed already):
```
pyenv install
```
2. Install pipenv:
```
pip install pipenv
```
3. Install python dependencies required for templates:
```
pipenv install --dev
```


## Customize Prediction pipeline

Let's open the XGBoost prediction pipeline & walk through different components:
<walkthrough-editor-open-file filePath="./pipelines/xgboost/prediction/pipeline.py"
                              text="XGBoost Prediction Pipeline">
</walkthrough-editor-open-file>.

## Step 1/3: Data Ingestion

TODO: Add description for SQL queries

## Step 2/3: Tensorflow Data Validation

TODO: Add description around skew detection, dataflow usage etc

## Step 3/3: Batch Prediction

TODO: Add description for batch prediction inc. machine configurations


## Customize Prediction config

TODO: Add steps required to update payload files


## Run Prediction pipeline on Vertex

Now that the pipeline is all set for execution, you can run the training pipeline on Vertex with a command as simple as:
```
make run PIPELINE_TEMPLATE=xgboost pipeline=prediction
```


## Congratulations

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You’re all set!

You can now track your ML Prediction pipeline from the Vertex Pipelines UI!
