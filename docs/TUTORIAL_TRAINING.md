# Vertex Pipelines E2E Sample - ML Training


## Introduction

It is hard to productionize data science use cases, especially because the journey from experimentation lacks standardisation. 

This GitHub repository bundles reusable code and provides the creation of a MLOps platform via a template-driven approach allowing to:

- **Create a new use case from a template**: Create a new ML training pipeline and batch prediction pipeline based on a template (XGBoost/ Tensorflow).
- **Deploy a pipeline to a production environment**: Deploy a new or updated pipeline to a production environment allowing for orchestration, schedules and triggers.


## Let's get started!

This guide will show you how to use the XGBoost template from this GitHub repository & quickly run an end-to-end Vertex ML Training Pipeline on the public **Chicago Taxi dataset**.

**Pre-requisites**:
- You have a Google Cloud Platform account + Google project
- You have enabled the following API's for this GCP project
    - Vertex AI
    - Cloud BigQuery
    - Cloud Storage

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
3. Install python dependencies (*Cloud Shell default - Python 3.9*):
```sh
pipenv --python /usr/bin/python3.9 install --skip-lock
```


## Training pipeline - Overview

Let's open the
<walkthrough-editor-open-file filePath="pipelines/xgboost/training/pipeline.py">XGBoost Training Pipeline</walkthrough-editor-open-file>

& walk through the following 5 building blocks of this Vertex Training pipeline:
- **SQL Queries in BigQuery**
- **Tensorflow Data Validation**
- **Model Training**
- **Model Evaluation**
- **Model Deployment**: *Champion-Challenger Approach*


## SQL Queries in BigQuery - Overview

First step for this training pipeline is to create a train-test-validation data which can be used by subsequent pipeline components.

BigQuery is leveraged for this data processing with SQL queries in 3 stages:

1. **Data Ingestion**

    This stage takes source data *(stored as a BigQuery table)*, applies some basic data operations using SQL queries & outputs a BigQuery table which is ready for train-test-validation splits.

    Some of these data operations can include (but not limited to):
    - Column selection or creation
    - Filtering of rows basis business logic
    
2. **Data Splitting**

    Once the data ingestion SQL creates a BigQuery table, this table can now be split into individual train-validation-test BigQuery tables using SQL queries.
    You can define the splitting techniques & ratios as required *(random sampling, stratified sampling)*

3. **Data Cleaning**

    Once the training data is available as a BigQuery table, you can now run SQL to clean the data as required.
    These cleaning operations can include removal of nulls, missing value imputation etc

Now that we understand how BigQuery is used in the training pipeline, click on **Next** to find out how to configure pipeline components for the same! 

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
        target_column=label_column_name,
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

TFDV is leveraged in the training pipeline in 3 key ways:
1. **Compute** descriptive **statistics**
2. **Visualize** these generated statistcis
3. Validate data for any **anomalies** & flag them 

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

Now, the most important aspect of using TFDV is to use the previously generated statistics & flag any data anomalies.
This aspect is captured in the following 2 pipeline components:

**Validate Schema**
```py
validated_schema = validate_schema(
    statistics=gen_statistics.output, schema_path=tfdv_schema_path,
).set_display_name("Validate data schema")
```

**Show Anomalies**
```py
anomalies = show_anomalies(
    anomalies=validated_schema.output,
    fail_on_anomalies=True,
).set_display_name("Show anomalies")
```

An anomaly can be flagged for the following reasons:
- % of Missing values greater than a threshold
- Datatype mismatch
- Expected columns which are missing
- Many others....

You can always finetune the TFDV schema to ensure data quality checks match your requirements

<walkthrough-footnote>TFDV 4/4</walkthrough-footnote>

## Model Training - Overview

Model training is captured in the training pipeline in 2 aspects:

1. **Update the Training component as per your requirements**

    Base code for model training exists in this file: <walkthrough-editor-open-file filePath="pipelines/kfp_components/xgboost/train.py">XGBoost Training Component</walkthrough-editor-open-file>

    This file contains implementation of an **XGBoost Regressor model** with **scikit-learn preprocessing** for feature engineering. The component outputs a scikit-learn pipeline object (saved as a joblib file) into Google Cloud Storage. 

 2. **Call training component in pipeline with your required model parameters**
 
    Once your training code is updated, the component just needs to be called in the pipeline file

<walkthrough-footnote>Model Training 1/3</walkthrough-footnote>

## Model Training - Component

Let's open the training component for a deep-dive: <walkthrough-editor-open-file filePath="pipelines/kfp_components/xgboost/train.py">XGBoost Training Component</walkthrough-editor-open-file>

First, feature engineering is added to a *ColumnTransformer* in a *scikit-learn pipeline* as follows:
```py
all_transformers = [
    ("numeric_scaling", StandardScaler(), num_indices),
    (
        "one_hot_encoding",
        OneHotEncoder(handle_unknown="ignore"),
        cat_indices_onehot,
    ),
]

preprocesser = ColumnTransformer(
    transformers=all_transformers
)
```

- **Normalization** is applied to all numeric features
- **One-hot Encoding** is applied to categorical features

Next, an *XGBRegressor* is added to this *scikit-learn pipeline* as follows:
```py
xgb_model = XGBRegressor(**model_params)

pipeline = Pipeline(
    steps=[
        ("feature_engineering", preprocesser),
        ("train_model", xgb_model)
    ]
)
```

This model training code can be modified as per use-case requirements

<walkthrough-footnote>Model Training 2/3</walkthrough-footnote>

## Model Training - Pipeline Addition

Now that the model training code/component is ready for use, you can call this component in the <walkthrough-editor-open-file filePath="pipelines/xgboost/training/pipeline.py">XGBoost Training Pipeline</walkthrough-editor-open-file> as follows:

1. **Define required model parameters**:
    ```py
    model_params = dict(
        n_estimators=200,
        early_stopping_rounds=10,
        objective="reg:squarederror",
        booster="gbtree",
        learning_rate=0.3,
        min_split_loss=0,
        max_depth=6,
    )
    ```

2. **Pass these defined model parameters to the pipeline component**
    ```py
    train_model = (
        custom_train_job(
            training_data=train_dataset.outputs["dataset"],
            validation_data=valid_dataset.outputs["dataset"],
            file_pattern=file_pattern,
            label_name=label_column_name,
            model_params=json.dumps(model_params),
            # Training wrapper specific parameters
            project=project_id,
            location=project_location,
        )
        .after(train_dataset)
        .set_display_name("Vertex Training for XGB model")
    )
    ```

This component will take training & validation data *(in Cloud Storage)* as input & execute a model training job on Vertex AI

<walkthrough-footnote>Model Training 3/3</walkthrough-footnote>

## Model Evaluation - Overview

Now that model training is configured in the pipeline, next step would be to evaluate this trained model.

This is done in 2 steps or components in the pipeline:
1. **Predict test data** with the trained model -
```py
predictions = predict_xgboost_model(
    test_dataset.outputs["dataset"],
    model,
    label_column_name=label_column_name,
    predictions_column_name=pred_column_name,
    file_pattern=file_pattern,
).set_display_name("Predict test data")
```

2. **Evaluate model** based on these predictions -
```py
eval_metrics = calculate_eval_metrics(
    csv_file=predictions.output,
    metrics_names=json.dumps(metrics_names),
    label_column_name=label_column_name,
    pred_column_name=pred_column_name,
).set_display_name("Evaluate test metrics")
```

Model Evaluation is done using TensorFlow Model Analysis (TFMA) which is framework-agnostic.

<walkthrough-footnote>Model Evaluation 1/2</walkthrough-footnote>

## Model Evaluation - TFMA Features

TFMA provides flexibility for model evaluation in multiple areas, some of which include:

1. **Evaluate as many metrics as required**

TFMA comes with many pre-existing metrics that are readily available for you. These metrics can be applied for Regression, Binary/Multi-class/Multi-label Classification, Ranking etc

To update list of required metrics, you can edit the following list in the pipeline:
```py
metrics_names = ["MeanSquaredError", "<Other_Metrics>"]
```

2. **Evaluate on slices of data**

You can also add slicing specs as a parameter to the *calculate_eval_metrics* component as follows:

```py
slicing_specs=[
    # Option 1
    'feature_keys: ["payment_type"]',
    # Option 2
    'feature_values: [{key: "payment_type", value: "Cash"}]',
    # Option 3
    'feature_keys: ["company"] ' +
    'feature_values: [{key: "payment_type", value: "Cash"}]',
],
```

where:
- **Option 1** computes metrics for every distinct value of *payment_type*
- **Option 2** computes metrics when *payment_type=Cash*
- **Option 3** computes metrics when *payment_type=Cash* for every distinct value of *company*

<walkthrough-footnote>Model Evaluation 2/2</walkthrough-footnote>

## Model Deployment - Champion-Challenger Approach

Now that model training & evaluation has been configured, next logical pipeline component is to deploy the model.

With best practices for MLOps in mind, model deployment is driven by the **Champion-Challenger approach**

This approach works in 5 stages:
1. **Evaluate test data** with latest trained model as the **Challenger**
2. **Evaluate same test data** with existing model as the **Champion** (if it exists)
3. **Compare** evaluation metrics from steps 1+2
4. **If challenger model performs better, deploy it as the new champion**
5. **If champion model performs better, skip model deployment**

For more details on implementation of these stages in the pipeline, click on **Next**! 

<walkthrough-footnote>Model Deployment 1/3</walkthrough-footnote>

## Model Deployment - Compare Champion vs Challenger models

As described previously in the **Model evaluation** section, evaluation on test data applies for both Champion & Challenger models.

Once this evaluation is complete, performance comparison of the 2 models is captured in the pipeline as follows:

```py
compare_champion_challenger_models = compare_models(
    metrics=champion_eval_metrics.outputs["eval_metrics"],
    other_metrics=challenger_eval_metrics.outputs["eval_metrics"],
    evaluation_metric="mean_squared_error",
    higher_is_better=False,
    absolute_difference=0.1,
).set_display_name("Compare champion and challenger models")
```

Since this tutorial trains an *XGBRegressor*, model comparison is configured on **Mean Squared Error**.

If **Mean Squared Error** for the challenger model has improved/dropped by 0.1, it will be deployed as the new champion

Similarly, for a classification problem, you can compare on a metric like **AUC** where increase in the metric by a threshold can lead to model deployment

<walkthrough-footnote>Model Deployment 2/3</walkthrough-footnote>

## Model Deployment - Upload model to Vertex AI

Based on model comparison as mentioned in the previous step, if the challenger model performs better than the existing champion, the challenger is uploaded as **Vertex AI Model** in the pipeline as follows:

```py
# Upload model
upload_model(
    display_name=model_name,
    serving_container_image_uri=SKL_SERVING_CONTAINER_IMAGE_URI,
    model=model,
    project_id=project_id,
    project_location=project_location,
).set_display_name("Upload challenger model")
```

You can change the *serving_container_image* depending on the template used.

For this tutorial, since we are running the training pipeline for a *scikit-learn pipeline* with an *XGBoost model*, the serving container used is Google's pre-built image for `scikit-learn`

<walkthrough-footnote>Model Deployment 3/3</walkthrough-footnote>

## Customize Training Config - Overview

To quickly recap, we now understand:
- Structure of the Vertex Training pipeline
- Changes needed for the pipeline (if any)

As a final step, 2 key configuration aspects need updating before running the pipeline & seeing it in action!

These steps include:
1. **Updating the payload**

    For each pipeline, there is a JSON file that contains pipeline parameters (and some other parameters) required to run the pipeline in GCP environment.
    You can view and modify this payload file <walkthrough-editor-open-file filePath="pipelines/xgboost/training/payloads/dev.json">XGBoost Training Pipeline Payload</walkthrough-editor-open-file>
   
2. **Updating environment variables**

    While executing the Vertex pipeline from a local setup or in cloud shell, certain environment variables need updating before execution. This is done by renaming file `env.sh.example` in the base GitHub repository to `env.sh` & modifying it.
    You can rename, view and modify this bash file <walkthrough-editor-open-file filePath="env.sh.example">Environment Variables</walkthrough-editor-open-file>

<walkthrough-footnote>Customize Training Config 1/3</walkthrough-footnote>

## Customize Training Config - Payload

Let's open the file for
<walkthrough-editor-open-file filePath="pipelines/xgboost/training/payloads/dev.json">XGBoost Training Pipeline Payload</walkthrough-editor-open-file>
& update the following values:

```json
"data": {
    "project_id": "Your GCP Project name",
    "project_location": "Region where you want to run the Vertex pipeline",
    "pipeline_files_gcs_path": "Google Cloud Storage bucket where compiled pipelines will be saved",
    "model_name": "Any name for your final trained model",
    "tfdv_train_stats_path": "Google Cloud storage path where Training statistics will be saved",

    "ingestion_project_id": "Your GCP project name where source BigQuery data exists",
    "ingestion_dataset_id": "BigQuery dataset name where source table exists",

    "dataset_id": "Bigquery dataset name where all tables will be created",
    "dataset_location": "BigQuery dataset location"
}
```

<walkthrough-footnote>Customize Training Config 2/3</walkthrough-footnote>

## Customize Training Config - `env.sh`

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

<walkthrough-footnote>Customize Training Config 3/3</walkthrough-footnote>


## Run Training pipeline on Vertex

Now that the pipeline + configuration is all set up for execution, you can run the training pipeline on Vertex with a single command:
```sh
make run pipeline=training
```


## Congratulations

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You’re all set!

You can now click on the **Pipeline Job** link shown on your terminal & track your **ML Training pipeline** from the **Vertex Pipelines UI**!
