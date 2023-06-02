# training & prediction pipeline
table_prefix = "tf_"
model_name = "my-tf-model"

# training pipeline
train_pipeline_name = "train-tf"
train_preprocess_sql = "train_preprocess.sql"
train_label_column_name = "total_fare"
train_hparams = dict(
    batch_size=100,
    epochs=5,
    loss_fn="MeanSquaredError",
    optimizer="Adam",
    learning_rate=0.01,
    hidden_units=[(64, "relu"), (32, "relu")],
    distribute_strategy="single",
    early_stopping_epochs=5,
)
train_requirements = []
train_script = "train_tf_model.py"
train_container = (
    "europe-docker.pkg.dev/vertex-ai/training/tf-cpu.2-6:latest"  # noqa: E501
)
serve_container = (
    "europe-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-6:latest"  # noqa: E501
)
test_dataset_uri = ""

# prediction pipeline
predict_pipeline_name = "predict-tf"
predict_preprocess_sql = "predict_preprocess.sql"
predict_machine_type = "n1-standard-4"
predict_min_replicas = 1
predict_max_replicas = 1
monitoring_alert_email_addresses = []
monitoring_skew_config = {"defaultSkewThreshold": {"value": 0.001}}
instance_config = {"instanceType": "object"}
predict_job_name = "tf-predict"
