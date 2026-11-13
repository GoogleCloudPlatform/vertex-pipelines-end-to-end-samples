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


from types import SimpleNamespace
from unittest import mock

import pytest
from kfp.dsl import Artifact

import components

deploy_model = components.deploy_model.python_func

PROJECT = "test-project"
LOCATION = "europe-west2"
ENDPOINT_NAME = "my-endpoint"
ENDPOINT_ID = "456"
SERVICE_ACCOUNT = "vertex-pipelines@test-project.iam.gserviceaccount.com"
MODEL_RESOURCE = "projects/test-project/locations/europe-west2/models/123@1"


def _make_vertex_model(tmp_path, resource_name: str = MODEL_RESOURCE) -> Artifact:
    artifact = Artifact(uri=str(tmp_path / "vertex_model"))
    artifact.metadata["resourceName"] = resource_name
    return artifact


def _make_deployed_model(model_id: str, create_time: str):
    model = mock.MagicMock()
    model.id = model_id
    model.create_time = create_time
    return model


@pytest.fixture
def sdk_mocks():
    """Patch Vertex SDK symbols used inside deploy_model."""
    with mock.patch("google.cloud.aiplatform.init") as mock_init, mock.patch(
        "google.cloud.aiplatform.Model"
    ) as mock_model_cls, mock.patch(
        "google.cloud.aiplatform.Endpoint"
    ) as mock_endpoint_cls:
        yield SimpleNamespace(
            init=mock_init,
            Model=mock_model_cls,
            Endpoint=mock_endpoint_cls,
        )


def _configure_endpoint(
    sdk_mocks,
    *,
    existing_endpoint: bool = True,
    deployed_models=None,
):
    mock_model = mock.MagicMock()
    sdk_mocks.Model.return_value = mock_model

    mock_endpoint = mock.MagicMock()
    mock_endpoint.resource_name = (
        f"projects/{PROJECT}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    )
    mock_endpoint.list_models.return_value = list(deployed_models or [])
    logging_cfg = mock_endpoint.gca_resource.predict_request_response_logging_config
    logging_cfg.enabled = False
    logging_cfg.bigquery_destination.output_uri = ""

    if existing_endpoint:
        sdk_mocks.Endpoint.list.return_value = [mock_endpoint]
    else:
        sdk_mocks.Endpoint.list.return_value = []
        sdk_mocks.Endpoint.create.return_value = mock_endpoint

    return mock_model, mock_endpoint


def _call_deploy(
    tmp_path,
    *,
    traffic_percentage: int = 100,
    **kwargs,
):
    return deploy_model(
        vertex_model=_make_vertex_model(tmp_path),
        project=PROJECT,
        location=LOCATION,
        endpoint_name=ENDPOINT_NAME,
        service_account=SERVICE_ACCOUNT,
        traffic_percentage=traffic_percentage,
        **kwargs,
    )


def test_creates_endpoint_when_none_exists(tmp_path, sdk_mocks):
    mock_model, _ = _configure_endpoint(sdk_mocks, existing_endpoint=False)

    result = _call_deploy(tmp_path)

    sdk_mocks.Endpoint.create.assert_called_once()
    create_kwargs = sdk_mocks.Endpoint.create.call_args[1]
    assert create_kwargs["display_name"] == ENDPOINT_NAME
    assert create_kwargs["project"] == PROJECT
    assert create_kwargs["location"] == LOCATION
    mock_model.deploy.assert_called_once()
    assert result[0] == ENDPOINT_ID
    assert result[1] == ""


def test_uses_existing_endpoint(tmp_path, sdk_mocks):
    mock_model, _ = _configure_endpoint(sdk_mocks, existing_endpoint=True)

    result = _call_deploy(tmp_path)

    sdk_mocks.Endpoint.create.assert_not_called()
    mock_model.deploy.assert_called_once()
    assert result[0] == ENDPOINT_ID
    assert result[1] == ""


def test_direct_deploy_when_no_models_on_endpoint(tmp_path, sdk_mocks):
    mock_model, mock_endpoint = _configure_endpoint(
        sdk_mocks, existing_endpoint=True, deployed_models=[]
    )

    _call_deploy(tmp_path, traffic_percentage=100)

    deploy_kwargs = mock_model.deploy.call_args[1]
    assert deploy_kwargs["endpoint"] is mock_endpoint
    assert deploy_kwargs["traffic_percentage"] == 100
    assert deploy_kwargs["service_account"] == SERVICE_ACCOUNT
    assert deploy_kwargs["sync"] is True
    assert "traffic_split" not in deploy_kwargs


def test_rolling_deploy_with_existing_model(tmp_path, sdk_mocks):
    existing = _make_deployed_model("existing-model-id", "2026-01-01T00:00:00Z")
    mock_model, _ = _configure_endpoint(
        sdk_mocks, existing_endpoint=True, deployed_models=[existing]
    )

    _call_deploy(tmp_path, traffic_percentage=80)

    deploy_kwargs = mock_model.deploy.call_args[1]
    assert deploy_kwargs["service_account"] == SERVICE_ACCOUNT
    assert deploy_kwargs["traffic_split"] == {
        "0": 80,
        "existing-model-id": 20,
    }
    assert "traffic_percentage" not in deploy_kwargs


def test_undeploys_models_older_than_two_most_recent(tmp_path, sdk_mocks):
    models = [
        _make_deployed_model(f"model-{i}", ts)
        for i, ts in enumerate(["2026-01-01", "2026-02-01", "2026-03-01"])
    ]
    mock_model, mock_endpoint = _configure_endpoint(
        sdk_mocks, existing_endpoint=True, deployed_models=[models[0]]
    )
    # First list (pre-deploy) has one model; second list (post-deploy) has three.
    mock_endpoint.list_models.side_effect = [[models[0]], models]

    _call_deploy(tmp_path)

    mock_endpoint.undeploy.assert_called_once_with("model-0")


def test_raises_on_multiple_endpoints(tmp_path, sdk_mocks):
    sdk_mocks.Endpoint.list.return_value = [mock.MagicMock(), mock.MagicMock()]

    with pytest.raises(RuntimeError, match="Multiple endpoints"):
        _call_deploy(tmp_path)


def test_loads_correct_model_resource(tmp_path, sdk_mocks):
    _configure_endpoint(sdk_mocks, existing_endpoint=True)

    _call_deploy(tmp_path)

    sdk_mocks.Model.assert_called_once_with(MODEL_RESOURCE)
    sdk_mocks.init.assert_called_once_with(project=PROJECT, location=LOCATION)


def test_creates_endpoint_with_request_response_logging(tmp_path, sdk_mocks):
    mock_model, mock_endpoint = _configure_endpoint(sdk_mocks, existing_endpoint=False)
    expected_uri = "bq://test-project.logging_my_endpoint.request_response_logging"
    logging_cfg = mock_endpoint.gca_resource.predict_request_response_logging_config
    logging_cfg.enabled = True
    logging_cfg.bigquery_destination.output_uri = expected_uri

    result = _call_deploy(
        tmp_path,
        enable_request_response_logging=True,
        logging_sampling_rate=0.5,
    )

    create_kwargs = sdk_mocks.Endpoint.create.call_args[1]
    assert create_kwargs["enable_request_response_logging"] is True
    assert create_kwargs["request_response_logging_sampling_rate"] == 0.5
    assert create_kwargs["request_response_logging_bq_destination_table"] == (
        expected_uri
    )
    assert result[1] == expected_uri
    mock_model.deploy.assert_called_once()


def test_existing_endpoint_without_logging_raises_when_requested(
    tmp_path, sdk_mocks
):
    _configure_endpoint(sdk_mocks, existing_endpoint=True)

    with pytest.raises(RuntimeError, match="no logging destination"):
        _call_deploy(tmp_path, enable_request_response_logging=True)

    sdk_mocks.Endpoint.create.assert_not_called()


def test_falls_back_to_requested_logging_uri_when_sdk_omits_it(tmp_path, sdk_mocks):
    _configure_endpoint(sdk_mocks, existing_endpoint=False)

    result = _call_deploy(tmp_path, enable_request_response_logging=True)

    create_kwargs = sdk_mocks.Endpoint.create.call_args[1]
    assert create_kwargs["request_response_logging_bq_destination_table"] == (
        "bq://test-project.logging_my_endpoint.request_response_logging"
    )
    assert result[1] == (
        "bq://test-project.logging_my_endpoint.request_response_logging"
    )
