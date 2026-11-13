# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from unittest import mock

from kfp.dsl import Artifact

import components

predict_on_endpoint = components.predict_on_endpoint.python_func

EXPECTED_INSTANCE_COUNT = 10
EXPECTED_FIRST_INSTANCE = {
    "dayofweek": 4.0,
    "hourofday": 14.0,
    "trip_distance": 3210.5,
    "trip_miles": 2.1,
    "trip_seconds": 720.0,
    "payment_type": "Credit Card",
    "company": "Flash Cab",
}


@mock.patch("google.cloud.aiplatform.Endpoint")
@mock.patch("google.cloud.aiplatform.init")
def test_predict_on_endpoint(mock_init, mock_endpoint_cls, tmp_path):
    mock_endpoint = mock.MagicMock()
    mock_response = mock.MagicMock()
    mock_response.predictions = [42.0]
    mock_endpoint.predict.return_value = mock_response
    mock_endpoint_cls.return_value = mock_endpoint

    predictions_artifact = Artifact(uri=str(tmp_path / "predictions.json"))

    predict_on_endpoint(
        endpoint_id="12345",
        project="my-project",
        predictions=predictions_artifact,
        location="europe-west2",
        num_requests=1,
    )

    mock_init.assert_called_once_with(project="my-project", location="europe-west2")
    mock_endpoint_cls.assert_called_once_with(
        endpoint_name="projects/my-project/locations/europe-west2/endpoints/12345",
    )
    mock_endpoint.predict.assert_called_once()
    instances_sent = mock_endpoint.predict.call_args[1]["instances"]
    assert len(instances_sent) == EXPECTED_INSTANCE_COUNT
    assert instances_sent[0] == EXPECTED_FIRST_INSTANCE

    with open(predictions_artifact.path) as f:
        result = json.load(f)
    assert result == {"predictions": [42.0]}


@mock.patch("google.cloud.aiplatform.Endpoint")
@mock.patch("google.cloud.aiplatform.init")
def test_predict_on_endpoint_custom_location(mock_init, mock_endpoint_cls, tmp_path):
    mock_endpoint = mock.MagicMock()
    mock_response = mock.MagicMock()
    mock_response.predictions = [99.0]
    mock_endpoint.predict.return_value = mock_response
    mock_endpoint_cls.return_value = mock_endpoint

    predictions_artifact = Artifact(uri=str(tmp_path / "predictions.json"))

    predict_on_endpoint(
        endpoint_id="111",
        project="my-project",
        predictions=predictions_artifact,
        location="us-central1",
        num_requests=1,
    )

    mock_init.assert_called_once_with(project="my-project", location="us-central1")
    mock_endpoint_cls.assert_called_once_with(
        endpoint_name="projects/my-project/locations/us-central1/endpoints/111",
    )


@mock.patch("google.cloud.aiplatform.Endpoint")
@mock.patch("google.cloud.aiplatform.init")
def test_predict_on_endpoint_multiple_requests(mock_init, mock_endpoint_cls, tmp_path):
    mock_endpoint = mock.MagicMock()
    mock_response = mock.MagicMock()
    mock_response.predictions = [1.0]
    mock_endpoint.predict.return_value = mock_response
    mock_endpoint_cls.return_value = mock_endpoint

    predictions_artifact = Artifact(uri=str(tmp_path / "predictions.json"))

    predict_on_endpoint(
        endpoint_id="12345",
        project="my-project",
        predictions=predictions_artifact,
        num_requests=3,
    )

    assert mock_endpoint.predict.call_count == 3
    with open(predictions_artifact.path) as f:
        result = json.load(f)
    assert result == {"predictions": [1.0, 1.0, 1.0]}
