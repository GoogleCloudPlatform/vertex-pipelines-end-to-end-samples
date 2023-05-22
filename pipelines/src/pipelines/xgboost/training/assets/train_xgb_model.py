import argparse
from pathlib import Path

import joblib
import json
import os
import logging

import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OrdinalEncoder, OneHotEncoder
from xgboost import XGBRegressor

logging.basicConfig(level=logging.DEBUG)

# used for monitoring during prediction time
TRAINING_DATASET_INFO = "training_dataset.json"
# numeric/categorical features in Chicago trips dataset to be preprocessed
NUM_COLS = ["dayofweek", "hourofday", "trip_distance", "trip_miles", "trip_seconds"]
ORD_COLS = ["company"]
OHE_COLS = ["payment_type"]


def split_xy(df: pd.DataFrame, label: str) -> (pd.DataFrame, pd.Series):
    """Split dataframe into X and y."""
    return df.drop(columns=[label]), df[label]


def indices_in_list(elements: list, base_list: list) -> list:
    """Get indices of specific elements in a base list"""
    return [idx for idx, elem in enumerate(base_list) if elem in elements]


parser = argparse.ArgumentParser()
parser.add_argument("--train_data", type=str, required=True)
parser.add_argument("--valid_data", type=str, required=True)
parser.add_argument("--test_data", type=str, required=True)
parser.add_argument("--model", default=os.getenv("AIP_MODEL_DIR"), type=str, help="")
parser.add_argument("--metrics", type=str, required=True)
parser.add_argument("--hparams", default={}, type=json.loads)
args = parser.parse_args()

if args.model.startswith("gs://"):
    args.model = Path("/gcs/" + args.model[5:])

logging.info("Read csv files into dataframes")
df_train = pd.read_csv(args.train_data)
df_valid = pd.read_csv(args.valid_data)
df_test = pd.read_csv(args.test_data)

logging.info("Split dataframes")
label = args.hparams["label"]
X_train, y_train = split_xy(df_train, label)
X_valid, y_valid = split_xy(df_valid, label)
X_test, y_test = split_xy(df_test, label)

logging.info("Get the number of unique categories for ordinal encoded columns")
ordinal_columns = X_train[ORD_COLS]
n_unique_cat = ordinal_columns.nunique()

logging.info("Get indices of columns in base data")
col_list = X_train.columns.tolist()
num_indices = indices_in_list(NUM_COLS, col_list)
cat_indices_onehot = indices_in_list(OHE_COLS, col_list)
cat_indices_ordinal = indices_in_list(ORD_COLS, col_list)

ordinal_transformers = [
    (
        f"ordinal encoding for {ord_col}",
        OrdinalEncoder(
            handle_unknown="use_encoded_value", unknown_value=n_unique_cat[ord_col]
        ),
        [ord_index],
    )
    for ord_col in ORD_COLS
    for ord_index in cat_indices_ordinal
]
all_transformers = [
    ("numeric_scaling", StandardScaler(), num_indices),
    (
        "one_hot_encoding",
        OneHotEncoder(handle_unknown="ignore"),
        cat_indices_onehot,
    ),
] + ordinal_transformers

logging.info("Build sklearn preprocessing steps")
preprocesser = ColumnTransformer(transformers=all_transformers)
logging.info("Build sklearn pipeline with XGBoost model")
xgb_model = XGBRegressor(**args.hparams)

pipeline = Pipeline(
    steps=[("feature_engineering", preprocesser), ("train_model", xgb_model)]
)

logging.info("Transform validation data")
valid_preprocesser = preprocesser.fit(X_train)
X_valid_transformed = valid_preprocesser.transform(X_valid)

logging.info("Fit model")
pipeline.fit(X_train, y_train, train_model__eval_set=[(X_valid_transformed, y_valid)])

logging.info("Predict test data")
y_pred = pipeline.predict(X_test)
y_pred = y_pred.clip(0)

metrics = {
    "problemType": "regression",
    "rootMeanSquaredError": np.sqrt(metrics.mean_squared_error(y_test, y_pred)),
    "meanAbsoluteError": metrics.mean_absolute_error(y_test, y_pred),
    "meanAbsolutePercentageError": metrics.mean_absolute_percentage_error(
        y_test, y_pred
    ),
    "rSquared": metrics.r2_score(y_test, y_pred),
    "rootMeanSquaredLogError": np.sqrt(metrics.mean_squared_log_error(y_test, y_pred)),
}

logging.info(f"Save model to: {args.model}")
args.model.mkdir(parents=True)
joblib.dump(pipeline, str(args.model / "model.joblib"))

logging.info(f"Metrics: {metrics}")
with open(args.metrics, "w") as fp:
    json.dump(metrics, fp)

# Persist URIs of training file(s) for model monitoring in batch predictions
# See https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform_v1beta1.types.ModelMonitoringObjectiveConfig.TrainingDataset  # noqa: E501
# for the expected schema.
path = args.model / TRAINING_DATASET_INFO
training_dataset_for_monitoring = {
    "gcsSource": {"uris": [args.train_data]},
    "dataFormat": "csv",
    "targetField": label,
}
logging.info(f"Training dataset info: {training_dataset_for_monitoring}")

with open(path, "w") as fp:
    logging.info(f"Save training dataset info for model monitoring: {path}")
    json.dump(training_dataset_for_monitoring, fp)
