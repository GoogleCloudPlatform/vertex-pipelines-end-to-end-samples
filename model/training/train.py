# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pathlib import Path

import joblib
import logging

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OrdinalEncoder, OneHotEncoder
from xgboost import XGBRegressor

from .utils import indices_in_list, save_metrics, save_monitoring_info, split_xy


# used for monitoring during prediction time
TRAINING_DATASET_INFO = "training_dataset.json"
# numeric/categorical features in Chicago trips dataset to be preprocessed
NUM_COLS = ["dayofweek", "hourofday", "trip_distance", "trip_miles", "trip_seconds"]
ORD_COLS = ["company"]
OHE_COLS = ["payment_type"]


def train(
    input_path: str,
    input_test_path: str,
    output_train_path: str,
    output_valid_path: str,
    output_test_path: str,
    output_model: str,
    output_metrics: str,
    hparams: dict,
):

    logging.info("Read csv files into dataframes")
    df = pd.read_csv(input_path)

    logging.info("Split dataframes")
    label = hparams.pop("label")

    if input_test_path:
        # if static test data is used, only split into train & valid dataframes
        if input_test_path.startswith("gs://"):
            input_test_path = "/gcs/" + input_test_path[5:]
        df_train, df_valid = train_test_split(df, test_size=0.2, random_state=1)
        df_test = pd.read_csv(input_test_path)
    else:
        # otherwise, split into train, valid, and test dataframes
        df_train, df_test = train_test_split(df, test_size=0.2, random_state=1)
        df_train, df_valid = train_test_split(df_train, test_size=0.25, random_state=1)

    # create output folders
    for x in [output_metrics, output_train_path, output_test_path, output_test_path]:
        Path(x).parent.mkdir(parents=True, exist_ok=True)
    Path(output_model).mkdir(parents=True, exist_ok=True)

    df_train.to_csv(output_train_path, index=False)
    df_valid.to_csv(output_valid_path, index=False)
    df_test.to_csv(output_test_path, index=False)

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
    xgb_model = XGBRegressor(**hparams)

    pipeline = Pipeline(
        steps=[("feature_engineering", preprocesser), ("train_model", xgb_model)]
    )

    logging.info("Transform validation data")
    valid_preprocesser = preprocesser.fit(X_train)
    X_valid_transformed = valid_preprocesser.transform(X_valid)

    logging.info("Fit model")
    pipeline.fit(
        X_train, y_train, train_model__eval_set=[(X_valid_transformed, y_valid)]
    )

    logging.info("Predict test data")
    y_pred = pipeline.predict(X_test)
    y_pred = y_pred.clip(0)

    logging.info(f"Save model to: {output_model}")
    joblib.dump(pipeline, f"{output_model}/model.joblib")

    save_metrics(y_test, y_pred, output_metrics)
    save_monitoring_info(
        output_train_path, label, f"{output_model}/{TRAINING_DATASET_INFO}"
    )
