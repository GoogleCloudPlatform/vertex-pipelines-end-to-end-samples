from os import environ as env

from dataclasses import dataclass


@dataclass(init=False, repr=True, frozen=True)
class Config:
    """Configuration for all pipelines."""

    project_id = env.get("VERTEX_PROJECT_ID")
    project_id_ingestion = env.get("VERTEX_PROJECT_ID")
    project_location = env.get("VERTEX_LOCATION")
    dataset_location = env.get("VERTEX_LOCATION")
    staging_bucket = env.get("VERTEX_PIPELINE_ROOT")
    pipeline_files_gcs_path = env.get("PIPELINE_FILES_GCS_PATH")
    resource_suffix = "_xgboost"
    model_name = "my-xgboost-model"
    time_col = "trip_start_timestamp"


@dataclass(init=False, repr=True, frozen=True)
class TrainingConfig(Config):
    """Configuration for training pipelines."""

    pipeline_name = "train"
    dataset_id_ingestion = "chicago_taxi_trips"
    dataset_id = "preprocessing"
    ingestion_table = "taxi_trips"
    ingested_table = "ingested_data_for_train" + Config.resource_suffix
    train_table = "train_data" + Config.resource_suffix
    valid_table = "valid_data" + Config.resource_suffix
    test_table = "test_data" + Config.resource_suffix
    timestamp = "2022-12-01 00:00:00"
    primary_metric = "rootMeanSquaredError"
    query_file = "train_preprocess.sql"
    label_col = "total_fare"
    hparams = dict(
        n_estimators=200,
        early_stopping_rounds=10,
        objective="reg:squarederror",
        booster="gbtree",
        learning_rate=0.3,
        min_split_loss=0,
        max_depth=6,
        label=label_col,
    )
    requirements = ["scikit-learn==0.24.0"]
    train_script = "train_xgb_model.py"
    train_container = "europe-docker.pkg.dev/vertex-ai/training/scikit-learn-cpu.0-23:latest"  # noqa: E501
    serve_container = "europe-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.0-24:latest"  # noqa: E501
    test_dataset_uri = ""


@dataclass(init=False, repr=True, frozen=True)
class PredictionConfig(Config):
    """Configuration for prediction pipelines."""

    pipeline_name = "predict"
    predict_job_name = "xgboost-predict"
    preprocessing_dataset_id = "preprocessing"
    prediction_dataset_id = "prediction"
    ingestion_table = "taxi_trips"
    ingested_table = "ingested_data_for_predict" + Config.resource_suffix
    timestamp = "2022-12-01 00:00:00"
    query_file = "predict_preprocess.sql"
    machine_type = "n1-standard-4"
    min_replicas = 1
    max_replicas = 1
    monitoring_alert_email_addresses = []
    monitoring_skew_config = {"defaultSkewThreshold": {"value": 0.001}}
    instance_config = {}
