# Vertex Pipelines E2E Sample - ML Prediction


## Introduction

It is hard to productionize data science use cases, especially because the journey from experimentation lacks standardisation. 

This GitHub repository bundles reusable code and provides the creation of a MLOps platform via a template-driven approach allowing to:

- **Create a new use case from a template**: Create a new ML training pipeline and batch prediction pipeline based on a template (XGBoost/ Tensorflow).
- **Deploy a pipeline to a production environment**: Deploy a new or updated pipeline to a production environment allowing for orchestration, schedules and triggers.


## Let's get started!

This guide will show you how to use the XGBoost template from this GitHub repository & quickly run an end-to-end Vertex ML Prediction Pipeline on the public **Chicago Taxi dataset**.

**Pre-requisites**:

- You have a Google Cloud Platform account + Google project
- You have enabled the following API's for this GCP project
    - Vertex AI
    - Cloud BigQuery
    - Cloud Storage
- You have run a Vertex Training pipeline from the previous tutorial

**Time to complete**: <walkthrough-tutorial-duration duration="45"></walkthrough-tutorial-duration>


## Project Setup

Google Cloud organizes resources into projects. This allows you to collect all of the related resources for a single application in one place.

Begin by creating a new project or selecting an existing project for this tutorial.

<walkthrough-project-setup></walkthrough-project-setup>


Set this project in your cloud shell with the following command:
```sh
gcloud config set project <walkthrough-project-name/>
```


## Package Installation

The template requires certain python packages which can be installed with the following commands:

1. Install pipenv for package dependency management:
```sh
pip install pipenv
```
2. Add `pipenv` to your `PATH` variable
```sh
export PATH="$HOME/.local/bin:$PATH"
```
3. Install python dependencies:
```sh
pipenv install --skip-lock
```


## Prediction Pipeline - Overview

Let's open the
<walkthrough-editor-open-file filePath="pipelines/xgboost/prediction/pipeline.py">XGBoost Prediction Pipeline</walkthrough-editor-open-file>

& walk through the following 3 building blocks of this Vertex Prediction pipeline:
- **SQL Queries in BigQuery**
- **Tensorflow Data Validation**
- **Batch Prediction**

## SQL Queries in BigQuery - Overview

Similar to the training pipeline, first step for this prediction pipeline is to create the base data required for predictions.

BigQuery is leveraged for this data preparation/ processing with a SQL query. This SQL query will contain data operations similar to the **Data Ingestion** query in the Training pipeline.

For more details on how this SQL query can be configured as a component in the pipeline, click on **Next**!

<walkthrough-footnote>SQL Queries in BigQuery 1/2</walkthrough-footnote>

## SQL Queries in BigQuery - Pipeline Configuration

SQL Queries are added to components in the pipeline in 3 steps:

1. **Create templated SQL Queries**

    You can create a folder with all SQL queries & add placeholders as required. These placeholders can be replaced by input strings while rendering queries in the pipeline.
    Query templating is done using Jinja. Jinja is a Python package primarily used for templating.

2. **Generate queries in the pipeline from SQL template**

    You can call these templated SQL queries in the pipeline & render them as follows:
    ```py
    ingest_query = generate_query(
        queries_folder / "ingest.sql",
        source_dataset=f"{ingestion_project_id}.{ingestion_dataset_id}",
        source_table=ingestion_table,
    )
    ```
    where all parameters in this component are placeholders in the SQL query

3. **Call the BigQuery component to run the query & create a table**

    Now that SQL queries are rendered, you can pass these queries to a BigQuery component in the pipeline & create tables as follows:
    ```py
    kwargs = dict(
        bq_client_project_id=project_id,
        destination_project_id=project_id,
        dataset_id=dataset_id,
        query_job_config=json.dumps(
            dict(write_disposition="WRITE_TRUNCATE")
        ),
    )
    ingest = bq_query_to_table(
        query=ingest_query,
        table_id=ingested_table,
        **kwargs,
    ).set_display_name("Ingest data")
    ```

<walkthrough-footnote>SQL Queries in BigQuery 2/2</walkthrough-footnote>


## Tensorflow Data Validation - Overview

TensorFlow Data Validation (TFDV) library enables robust  ways to validate your data & flag any data anomalies.

TFDV is leveraged in the prediction pipeline in 3 key ways:
1. **Compute** descriptive **statistics**
2. **Visualize** these generated statistcis
3. **Compare prediction** data statistics with **training** data statistics to:
    - Detect any **data skew**
    - Flag any other **data anomalies**

<walkthrough-footnote>TFDV 1/4</walkthrough-footnote>

## Tensorflow Data Validation - Generate Statistics

The following component code snippet in the pipeline generates statistics for your dataset & uses these statistics for subsequent steps:

```py
# generate statistics
gen_statistics = generate_statistics(
    dataset=ingested_dataset.outputs["dataset"],
    file_pattern=file_pattern,
).set_display_name("Generate data statistics")
```

These statistics can include:
- Count/Mean/Min/Max/... for numeric features
- Distribution per category for categorical features
- % of missing values
- And many others

You can also use Cloud Dataflow to generate statistics for large data volumes by simply adding this parameter to the pipeline component

```py
use_dataflow=True
```

<walkthrough-footnote>TFDV 2/4</walkthrough-footnote>

## Tensorflow Data Validation - Visualize Statistics

The following component code snippet in the pipeline creates visualizations for previously generated statistics:

```py
# visualise statistics
visualised_statistics = visualise_statistics(
    statistics=gen_statistics.output,
    statistics_name="Data Statistics",
).set_display_name("Visualise data statistics")
```

Output from this component is basically an interactive HTML view for exploring statistics.

Some cool things included in this interactive view are:
- Feature distributions
- Deciles
- Dropdowns for selective analysis
- Many others....

<walkthrough-footnote>TFDV 3/4</walkthrough-footnote>

## Tensorflow Data Validation - Show Anomalies

Now, the most important aspect of using TFDV in a prediction pipeline is to compare statistics of prediction VS training data & flag any data skew + anomalies.
This aspect is captured in the following 2 pipeline components:

**Validate Skew**
```py
validated_skew = validate_skew(
    training_statistics_path=tfdv_train_stats_path,
    schema_path=tfdv_schema_path,
    serving_statistics=serving_stats.output,
    environment="SERVING",
).set_display_name("Validate data skew")
```

**Show Anomalies**
```py
anomalies = show_anomalies(
    anomalies=validated_skew.output,
    fail_on_anomalies=True,
).set_display_name("Show anomalies")
```

An anomaly can be flagged for the following reasons:
- Skew in data distributions between Prediction & Training data
- % of Missing values greater than a threshold
- Datatype mismatch
- Expected columns which are missing
- Many others....

You can always finetune the TFDV schema to ensure data quality checks match your requirements

<walkthrough-footnote>TFDV 4/4</walkthrough-footnote>

## Batch Prediction

Assuming that you have a trained XGBoost model uploaded to Vertex from the training pipeline (previous tutorial), you can now leverage this model to run *Batch Predictions* on *Vertex AI*

**Vertex Batch Predictions** takes a BigQuery table as input & outputs a BigQuery table with the input features + predictions.

Batch prediction as a component is configured in the pipeline as follows:
```py
batch_prediction = (
    ModelBatchPredictOp(
        project=project_id,
        job_display_name="my-display-name",
        location=project_location,
        model=champion_model.outputs["model"],
        instances_format="bigquery",
        predictions_format="bigquery",
        bigquery_source_input_uri="BQ Input table",
        bigquery_destination_output_uri="BQ Output Dataset",
        machine_type="n1-standard-4,
        starting_replica_count=3,
        max_replica_count=10,
    )
    .after(anomalies, ingest)
    .set_display_name("Vertex Batch Prediction")
)
```

You can flexibly configure the machine configuration for this batch prediction job to truly unlock the power of horizontal scalability in Vertex

<walkthrough-footnote>Batch Prediction 1/1</walkthrough-footnote>

## Customize Prediction Config - Overview

To quickly recap, we now understand:
- Structure of the Vertex Prediction pipeline
- Changes needed for the pipeline (if any)

As a final step, 2 key configuration aspects need updating before running the pipeline & seeing it in action!

These steps include:
1. **Updating the payload**

    For each pipeline, there is a JSON file that contains pipeline parameters (and some other parameters) required to run the pipeline in GCP environment.
    You can view and modify this payload file <walkthrough-editor-open-file filePath="pipelines/xgboost/prediction/payloads/dev.json">XGBoost Prediction Pipeline Payload</walkthrough-editor-open-file>
   
2. **Updating environment variables**

    While executing the Vertex pipeline from a local setup or in cloud shell, certain environment variables need updating before execution. This is done by renaming file `env.sh.example` in the base GitHub repository to `env.sh` & modifying it.
    You can rename, view and modify this bash file <walkthrough-editor-open-file filePath="env.sh.example">Environment Variables</walkthrough-editor-open-file>

<walkthrough-footnote>Customize Prediction Config 1/3</walkthrough-footnote>

## Customize Prediction Config - Payload

Let's open the file for
<walkthrough-editor-open-file filePath="pipelines/xgboost/prediction/payloads/dev.json">XGBoost Prediction Pipeline Payload</walkthrough-editor-open-file>
& update the following values:

```json
"data": {
    "project_id": "Your GCP Project name",
    "project_location": "Region where you want to run the Vertex pipeline",
    "pipeline_files_gcs_path": "Google Cloud Storage bucket where compiled pipelines will be saved",
    "model_name": "Name of your final trained model (as defined in the executed training pipeline)",
    "tfdv_train_stats_path": "Google Cloud storage path where Training statistics are saved (as defined in the executed training pipeline)",

    "ingestion_project_id": "Your GCP project name where source BigQuery data exists",
    "ingestion_dataset_id": "BigQuery dataset name where source table exists",

    "dataset_id": "Bigquery dataset name where all tables will be created",
    "dataset_location": "BigQuery dataset location"
}
```

<walkthrough-footnote>Customize Prediction Config 2/3</walkthrough-footnote>

## Customize Prediction Config - `env.sh`

Let's rename the file `env.sh.example` to `env.sh` (in the base folder), open the file
<walkthrough-editor-open-file filePath="env.sh">Environment Variables</walkthrough-editor-open-file>
& update the following values:

```sh 
export PAYLOAD=dev.json
export PIPELINE_FILES_GCS_PATH= Google Cloud Storage bucket where compiled pipelines will be saved
export VERTEX_PIPELINE_ROOT=Google Cloud Storage bucket where Vertex pipeline outputs will be saved

export PIPELINE_TEMPLATE=xgboost

export VERTEX_LOCATION=Region where you want to run the Vertex pipeline
export VERTEX_PROJECT_ID=Your GCP project name
export VERTEX_SA_EMAIL=Your Vertex Service account email ID (can use the default Compute Engine SA if required)
```

<walkthrough-footnote>Customize Prediction Config 3/3</walkthrough-footnote>


## Run Prediction pipeline on Vertex

Now that the pipeline + configuration is all set up for execution, you can run the prediction pipeline on Vertex with a single command:
```sh
make run pipeline=prediction
```


## Congratulations

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You’re all set!

You can now click on the **Pipeline Job** link shown on your terminal & track your **ML Prediction pipeline** from the **Vertex Pipelines UI**!
