# training & prediction pipeline
table_prefix = "xgboost_"
model_name = "my-xgboost-model"

# training pipeline
train_pipeline_name = "train-xgboost"
train_preprocess_sql = "train_preprocess.sql"
train_label_column_name = "total_fare"
train_hparams = dict(
    n_estimators=200,
    early_stopping_rounds=10,
    objective="reg:squarederror",
    booster="gbtree",
    learning_rate=0.3,
    min_split_loss=0,
    max_depth=6,
    label=train_label_column_name,
)
train_requirements = ["scikit-learn==0.24.0"]
train_script = "train_xgb_model.py"
train_container = "europe-docker.pkg.dev/vertex-ai/training/scikit-learn-cpu.0-23:latest"  # noqa: E501
serve_container = (
    "europe-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.0-24:latest"  # noqa: E501
)
test_dataset_uri = ""

# prediction pipeline
predict_pipeline_name = "predict-xgboost"
predict_preprocess_sql = "predict_preprocess.sql"
predict_machine_type = "n1-standard-4"
predict_min_replicas = 1
predict_max_replicas = 1
monitoring_alert_email_addresses = []
monitoring_skew_config = {"defaultSkewThreshold": {"value": 0.001}}
instance_config = {}
predict_job_name = "xgboost-predict"
