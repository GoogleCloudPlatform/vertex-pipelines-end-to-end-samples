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
import logging
import json

import numpy as np
import pandas as pd
from sklearn import metrics


def split_xy(df: pd.DataFrame, label: str) -> (pd.DataFrame, pd.Series):
    """Split dataframe into X and y."""
    return df.drop(columns=[label]), df[label]


def indices_in_list(elements: list, base_list: list) -> list:
    """Get indices of specific elements in a base list"""
    return [idx for idx, elem in enumerate(base_list) if elem in elements]


def save_metrics(y_test: pd.DataFrame, y_pred: pd.DataFrame, output_path: str):
    """Save metrics in JSON format for Vertex AI Evaluation."""
    data = {
        "problemType": "regression",
        "rootMeanSquaredError": np.sqrt(metrics.mean_squared_error(y_test, y_pred)),
        "meanAbsoluteError": metrics.mean_absolute_error(y_test, y_pred),
        "meanAbsolutePercentageError": metrics.mean_absolute_percentage_error(
            y_test, y_pred
        ),
        "rSquared": metrics.r2_score(y_test, y_pred),
        "rootMeanSquaredLogError": np.sqrt(
            metrics.mean_squared_log_error(y_test, y_pred)
        ),
    }

    logging.info(f"Metrics: {metrics}")
    with open(output_path, "w") as fp:
        json.dump(data, fp)


def save_monitoring_info(train_path: str, label: str, output_path: str):
    """Persist URIs of training file(s) for model monitoring in batch predictions.
    For the expected schema see:
        https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform_v1beta1.types.ModelMonitoringObjectiveConfig.TrainingDataset  # noqa: E501
    """
    training_dataset_for_monitoring = {
        "gcsSource": {"uris": [train_path]},
        "dataFormat": "csv",
        "targetField": label,
    }
    logging.info(f"Training dataset info: {training_dataset_for_monitoring}")

    with open(output_path, "w") as fp:
        logging.info(f"Save training dataset info for model monitoring: {output_path}")
        json.dump(training_dataset_for_monitoring, fp)
