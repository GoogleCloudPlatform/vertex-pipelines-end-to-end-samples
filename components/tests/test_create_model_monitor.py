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

import sys
from types import SimpleNamespace
from unittest import mock

import pytest
from kfp.dsl import Artifact

import components

create_model_monitor = components.create_model_monitor.python_func

PROJECT = "test-project"
LOCATION = "europe-west2"
DISPLAY_NAME = "turbo-prediction-endpoint-monitor"
VERSIONED_DISPLAY_NAME = f"{DISPLAY_NAME}-v2"
MONITOR_RESOURCE_NAME = "projects/test-project/locations/europe-west2/modelMonitors/123"
MODEL_RESOURCE = "projects/test-project/locations/europe-west2/models/123@2"
MONITORED_FEATURES = {"trip_miles": "float", "company": "categorical"}


def _make_vertex_model(tmp_path, resource_name: str = MODEL_RESOURCE) -> Artifact:
    artifact = Artifact(uri=str(tmp_path / "vertex_model"))
    artifact.metadata["resourceName"] = resource_name
    return artifact


@pytest.fixture
def sdk_mocks():
    """Mock Vertex preview SDK imports used inside create_model_monitor."""
    mock_model_monitor_class = mock.MagicMock()
    mock_ml_monitoring = mock.MagicMock()
    mock_ml_monitoring.ModelMonitor = mock_model_monitor_class
    mock_preview = mock.MagicMock()
    mock_preview.ml_monitoring = mock_ml_monitoring
    mock_spec_schema = mock.MagicMock()
    mock_spec = mock.MagicMock(schema=mock_spec_schema)
    mock_vertexai = mock.MagicMock()

    mock_monitor = mock.MagicMock()
    mock_monitor.resource_name = MONITOR_RESOURCE_NAME
    mock_model_monitor_class.list.return_value = []
    mock_model_monitor_class.create.return_value = mock_monitor

    modules = {
        "vertexai": mock_vertexai,
        "vertexai.resources": mock.MagicMock(),
        "vertexai.resources.preview": mock_preview,
        "vertexai.resources.preview.ml_monitoring": mock_ml_monitoring,
        "vertexai.resources.preview.ml_monitoring.spec": mock_spec,
        "vertexai.resources.preview.ml_monitoring.spec.schema": mock_spec_schema,
    }
    with mock.patch.dict(sys.modules, modules):
        yield SimpleNamespace(
            ModelMonitor=mock_model_monitor_class,
            monitor=mock_monitor,
            vertexai=mock_vertexai,
        )


def _call_create(tmp_path, sdk_mocks, resource_name=MODEL_RESOURCE):
    return create_model_monitor(
        vertex_model=_make_vertex_model(tmp_path, resource_name),
        project=PROJECT,
        location=LOCATION,
        display_name=DISPLAY_NAME,
        monitored_features=MONITORED_FEATURES,
    )


def test_creates_monitor_when_none_exists(tmp_path, sdk_mocks):
    result = _call_create(tmp_path, sdk_mocks)

    sdk_mocks.vertexai.init.assert_called_once_with(project=PROJECT, location=LOCATION)
    # versioned name, unversioned fallback, then full list
    assert sdk_mocks.ModelMonitor.list.call_count == 3
    sdk_mocks.ModelMonitor.list.assert_any_call(
        project=PROJECT,
        location=LOCATION,
        filter=f'display_name="{VERSIONED_DISPLAY_NAME}"',
    )
    sdk_mocks.ModelMonitor.list.assert_any_call(
        project=PROJECT,
        location=LOCATION,
        filter=f'display_name="{DISPLAY_NAME}"',
    )
    sdk_mocks.ModelMonitor.list.assert_any_call(
        project=PROJECT,
        location=LOCATION,
    )
    sdk_mocks.ModelMonitor.create.assert_called_once()
    create_kwargs = sdk_mocks.ModelMonitor.create.call_args.kwargs
    assert create_kwargs["model_name"] == (
        "projects/test-project/locations/europe-west2/models/123"
    )
    assert create_kwargs["model_version_id"] == "2"
    assert create_kwargs["display_name"] == VERSIONED_DISPLAY_NAME
    assert result[0] == MONITOR_RESOURCE_NAME


def test_reuses_existing_versioned_monitor(tmp_path, sdk_mocks):
    vertex = sdk_mocks.monitor.gca_resource.model_monitoring_target.vertex_model
    vertex.model = "projects/test-project/locations/europe-west2/models/123"
    vertex.model_version_id = "2"
    sdk_mocks.ModelMonitor.list.return_value = [sdk_mocks.monitor]

    result = _call_create(tmp_path, sdk_mocks)

    sdk_mocks.ModelMonitor.create.assert_not_called()
    assert result[0] == MONITOR_RESOURCE_NAME


def test_does_not_reuse_unparseable_target(tmp_path, sdk_mocks):
    opaque = mock.MagicMock()
    opaque.resource_name = (
        "projects/test-project/locations/europe-west2/modelMonitors/opaque"
    )
    opaque.gca_resource.model_monitoring_target = None
    opaque._gca_resource = None
    # First list (versioned name) returns opaque target → must not reuse.
    sdk_mocks.ModelMonitor.list.side_effect = [[opaque], [], []]

    _call_create(tmp_path, sdk_mocks)

    sdk_mocks.ModelMonitor.create.assert_called_once()


def test_unversioned_model_without_metadata_raises(tmp_path, sdk_mocks):
    with pytest.raises(ValueError, match="versionId is missing"):
        _call_create(
            tmp_path,
            sdk_mocks,
            resource_name="projects/test-project/locations/europe-west2/models/123",
        )


def test_unversioned_model_uses_metadata_version_id(tmp_path, sdk_mocks):
    vertex_model = _make_vertex_model(
        tmp_path,
        resource_name="projects/test-project/locations/europe-west2/models/123",
    )
    vertex_model.metadata["versionId"] = "33"

    create_model_monitor(
        vertex_model=vertex_model,
        project=PROJECT,
        location=LOCATION,
        display_name=DISPLAY_NAME,
        monitored_features=MONITORED_FEATURES,
    )

    create_kwargs = sdk_mocks.ModelMonitor.create.call_args.kwargs
    assert create_kwargs["model_version_id"] == "33"
    assert create_kwargs["display_name"] == f"{DISPLAY_NAME}-v33"


def test_does_not_reuse_display_name_monitor_for_other_version(tmp_path, sdk_mocks):
    other_version = mock.MagicMock()
    other_version.resource_name = (
        "projects/test-project/locations/europe-west2/modelMonitors/old-v1"
    )
    vertex = other_version.gca_resource.model_monitoring_target.vertex_model
    vertex.model = "projects/test-project/locations/europe-west2/models/123"
    vertex.model_version_id = "1"
    sdk_mocks.ModelMonitor.list.side_effect = [[other_version], [other_version], []]

    _call_create(tmp_path, sdk_mocks)

    sdk_mocks.ModelMonitor.create.assert_called_once()
    assert sdk_mocks.ModelMonitor.create.call_args.kwargs["model_version_id"] == "2"


def test_reuses_monitor_already_attached_to_model_version(tmp_path, sdk_mocks):
    existing_for_model = mock.MagicMock()
    existing_for_model.resource_name = (
        "projects/test-project/locations/europe-west2/modelMonitors/batch-old"
    )
    existing_for_model.display_name = "turbo-template-predict-job-monitoring"
    vertex = existing_for_model.gca_resource.model_monitoring_target.vertex_model
    vertex.model = "projects/test-project/locations/europe-west2/models/123"
    vertex.model_version_id = "2"
    sdk_mocks.ModelMonitor.list.side_effect = [[], [], [existing_for_model]]

    result = _call_create(tmp_path, sdk_mocks)

    sdk_mocks.ModelMonitor.create.assert_not_called()
    assert result[0] == existing_for_model.resource_name


def test_warns_on_schema_mismatch_when_reusing(tmp_path, sdk_mocks, caplog):
    import logging

    vertex = sdk_mocks.monitor.gca_resource.model_monitoring_target.vertex_model
    vertex.model = "projects/test-project/locations/europe-west2/models/123"
    vertex.model_version_id = "2"
    field = mock.MagicMock()
    field.name = "trip_miles"
    field.data_type = "categorical"
    sdk_mocks.monitor.gca_resource.model_monitoring_schema.feature_fields = [field]
    sdk_mocks.ModelMonitor.list.return_value = [sdk_mocks.monitor]

    with caplog.at_level(logging.WARNING):
        result = _call_create(tmp_path, sdk_mocks)

    assert result[0] == MONITOR_RESOURCE_NAME
    assert any("schema" in message.lower() for message in caplog.messages)
