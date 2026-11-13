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

from .utils import save_metrics, save_monitoring_info, split_xy
from shared.training_config import TrainingConfig


# used for monitoring during prediction time
TRAINING_DATASET_INFO = "training_dataset.json"


def train(
    input_path: str,
    input_test_path: str,
    output_train_path: str,
    output_valid_path: str,
    output_test_path: str,
    output_model: str,
    output_metrics: str,
    config: TrainingConfig,
):

    logging.info("Read csv files into dataframes")
    df = pd.read_csv(input_path)

    logging.info("Split dataframes")

    if input_test_path:
        # if static test data is used, only split into train & valid dataframes
        if input_test_path.startswith("gs://"):
            input_test_path = "/gcs/" + input_test_path[5:]
        df_train, df_valid = train_test_split(
            df, **config.get_split_params().get("train_test_split")
        )
        df_test = pd.read_csv(input_test_path)
    else:
        # otherwise, split into train, valid, and test dataframes
        df_train, df_test = train_test_split(
            df, **config.get_split_params().get("train_test_split")
        )
        df_train, df_valid = train_test_split(
            df_train, **config.get_split_params().get("train_valid_split")
        )

    # create output folders
    for x in [output_metrics, output_train_path, output_test_path, output_test_path]:
        Path(x).parent.mkdir(parents=True, exist_ok=True)
    Path(output_model).mkdir(parents=True, exist_ok=True)

    df_train.to_csv(output_train_path, index=False)
    df_valid.to_csv(output_valid_path, index=False)
    df_test.to_csv(output_test_path, index=False)

    X_train, y_train = split_xy(df_train, config.label)
    X_valid, y_valid = split_xy(df_valid, config.label)
    X_test, y_test = split_xy(df_test, config.label)

    logging.info("Build transformer list from config")
    all_transformers = config.get_transformers(X_train)

    logging.info("Build sklearn preprocessing steps")
    preprocesser = ColumnTransformer(transformers=all_transformers)
    logging.info("Build sklearn pipeline")
    model = config.get_model_class()(**config.get_model_params())

    pipeline = Pipeline(
        steps=[("feature_engineering", preprocesser), ("train_model", model)]
    )

    logging.info("Transform validation data")
    valid_preprocesser = preprocesser.fit(X_train)
    X_valid_transformed = valid_preprocesser.transform(X_valid)

    logging.info("Fit model")
    fit_kwargs = {}
    if config.use_eval_set:
        fit_kwargs["train_model__eval_set"] = [(X_valid_transformed, y_valid)]
    pipeline.fit(X_train, y_train, **fit_kwargs)

    logging.info("Predict test data")
    y_pred = pipeline.predict(X_test)
    y_pred = y_pred.clip(0)

    logging.info(f"Save model to: {output_model}")
    joblib.dump(pipeline, f"{output_model}/model.joblib")

    save_metrics(y_test, y_pred, output_metrics)
    save_monitoring_info(
        output_train_path,
        config.label,
        f"{output_model}/{TRAINING_DATASET_INFO}",
    )
