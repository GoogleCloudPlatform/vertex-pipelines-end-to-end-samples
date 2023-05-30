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
from unittest.mock import patch

from kfp.v2.dsl import Model


import vertex_components

update_best_model = vertex_components.update_best_model.python_func


def test_model_batch_predict(tmpdir):
    """
    Asserts model_batch_predict successfully creates requests given different arguments.
    """
    mock_model = Model(uri=tmpdir, metadata={"resourceName": ""})
    mock_message = {"metrics": {"rmse": 0.01}}

    with patch("google.cloud.aiplatform.Model",), patch(
        "google.cloud.aiplatform.model_evaluation.ModelEvaluation",
    ), patch("google.cloud.aiplatform.models.ModelRegistry",), patch(
        "google.protobuf.json_format.MessageToDict", return_value=mock_message
    ):

        (challenger_wins,) = update_best_model(
            challenger=mock_model,
            challenger_evaluation="",
            parent_model="",
            project_id="",
            project_location="",
            eval_metric="rmse",
            eval_lower_is_better=True,
        )
        assert not challenger_wins
