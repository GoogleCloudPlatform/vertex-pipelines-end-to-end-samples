# Copyright 2022 Google LLC
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

import numpy as np
import pandas as pd
from kfp.v2.dsl import Artifact, Dataset, Model


NUM_COLS = ["dayofweek", "hourofday", "trip_distance", "trip_miles", "trip_seconds"]
ORD_COLS = ["company"]
OHE_COLS = ["payment_type"]


def test_train_xgboost_model(tmpdir):
    """Test that the outputs of train_xgboost_model exist

    Args:
        tmpdir: built-in pytest tmpdir fixture
    Returns:
        None
    """
    from pipelines.kfp_components.xgboost import train_xgboost_model

    # generate random training/validation data
    n_rows = 100
    train_path = str(tmpdir.join("train.csv"))
    train_df = pd.DataFrame(
        np.random.rand(n_rows, len(NUM_COLS) + 1), columns=["label"] + NUM_COLS
    )
    train_df[ORD_COLS], train_df[OHE_COLS] = "test1", "test2"
    train_df.to_csv(train_path, index=False)

    # prepare arguments
    file_pattern = ""
    label_column_name = "label"
    xgb_params = dict(
        n_estimators=10,
        objective="reg:squarederror",
        booster="gbtree",
        learning_rate=0.3,
        min_split_loss=0,
        max_depth=6,
    )
    training_data = Dataset(uri=train_path)
    validation_data = Dataset(uri=train_path)
    model = Model(uri=str(tmpdir.join("/model")))
    metrics_artifact = Artifact(uri=str(tmpdir.join("metrics.json")))

    # invoke training
    train_xgboost_model(
        training_data=training_data,
        validation_data=validation_data,
        file_pattern=file_pattern,
        label_name=label_column_name,
        model_params=xgb_params,
        model=model,
        metrics_artifact=metrics_artifact,
    )

    # check outputs
    assert (tmpdir.join("/model") / "model.joblib").exists()
    assert (tmpdir / "metrics.json").exists()
