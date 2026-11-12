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

import re
import sys
from unittest import mock

import pytest
from google.cloud.aiplatform_v1beta1.types import model_monitoring_spec

import components

run_model_monitoring_job = components.run_model_monitoring_job.python_func

MONITOR_RESOURCE_NAME = "projects/test-project/locations/europe-west2/modelMonitors/123"
TRAINING_GCS_URI = "gs://bucket/train.csv"
TARGET_BQ_URI = "bq://test-project.logging_ep_456.request_response_logging"
MONITORED_FEATURES = {"trip_miles": "float", "company": "categorical"}

mock_created_monitoring_job = mock.Mock()
mock_created_monitoring_job.name = (
    f"{MONITOR_RESOURCE_NAME}/modelMonitoringJobs/mock-monitoring-job"
)


@pytest.fixture
def preview_sdk_mocks():
    """Mock Vertex preview spec builders used inside run_model_monitoring_job."""
    mock_spec_notification = mock.MagicMock()
    mock_spec_objective = mock.MagicMock()
    mock_spec_schema = mock.MagicMock()
    mock_ml_monitoring = mock.MagicMock()
    mock_preview = mock.MagicMock()
    mock_preview.ml_monitoring = mock_ml_monitoring
    mock_spec = mock.MagicMock(
        notification=mock_spec_notification,
        objective=mock_spec_objective,
        schema=mock_spec_schema,
    )
    mock_spec_objective.MonitoringInput.return_value._as_proto.return_value = (
        model_monitoring_spec.ModelMonitoringInput()
    )
    mock_spec_objective.TabularObjective.return_value._as_proto.return_value = (
        model_monitoring_spec.ModelMonitoringObjectiveSpec.TabularObjective()
    )
    mock_spec_notification.NotificationSpec.return_value._as_proto.return_value = (
        model_monitoring_spec.ModelMonitoringNotificationSpec()
    )

    modules = {
        "vertexai": mock.MagicMock(),
        "vertexai.resources": mock.MagicMock(),
        "vertexai.resources.preview": mock_preview,
        "vertexai.resources.preview.ml_monitoring": mock_ml_monitoring,
        "vertexai.resources.preview.ml_monitoring.spec": mock_spec,
        "vertexai.resources.preview.ml_monitoring.spec.notification": (
            mock_spec_notification
        ),
        "vertexai.resources.preview.ml_monitoring.spec.objective": mock_spec_objective,
        "vertexai.resources.preview.ml_monitoring.spec.schema": mock_spec_schema,
    }
    with mock.patch.dict(sys.modules, modules):
        yield mock_spec_objective


def _call_run(**overrides):
    kwargs = dict(
        project="test-project",
        location="europe-west2",
        model_monitor_name=MONITOR_RESOURCE_NAME,
        training_dataset_gcs_uri=TRAINING_GCS_URI,
        target_bq_table_uri=TARGET_BQ_URI,
        job_display_name="turbo-prediction-endpoint-monitoring",
        monitored_features=MONITORED_FEATURES,
        endpoint_id="456",
        notification_emails=["a@b.com"],
    )
    kwargs.update(overrides)
    return run_model_monitoring_job(**kwargs)


@mock.patch(
    "google.cloud.aiplatform_v1beta1.services.model_monitoring_service.ModelMonitoringServiceClient.create_model_monitoring_job",  # noqa: E501
    return_value=mock_created_monitoring_job,
)
def test_submits_fire_and_forget_monitoring_job(
    create_monitoring_job, preview_sdk_mocks
):
    result = _call_run()

    create_monitoring_job.assert_called_once()
    request = create_monitoring_job.call_args.kwargs["request"]
    assert request.parent == MONITOR_RESOURCE_NAME
    assert (
        request.model_monitoring_job.display_name
        == "turbo-prediction-endpoint-monitoring-run"
    )
    assert re.fullmatch(
        r"[a-z]([a-z0-9-]{0,61}[a-z0-9])?", request.model_monitoring_job_id
    )
    assert request.model_monitoring_job_id.startswith(
        "turbo-prediction-endpoint-monitoring-mon-"
    )
    preview_sdk_mocks.MonitoringInput.assert_any_call(
        gcs_uri=TRAINING_GCS_URI, data_format="csv"
    )
    preview_sdk_mocks.MonitoringInput.assert_any_call(
        endpoints=["projects/test-project/locations/europe-west2/endpoints/456"],
        window="1h",
    )
    assert result[0] == mock_created_monitoring_job.name


@mock.patch(
    "google.cloud.aiplatform_v1beta1.services.model_monitoring_service.ModelMonitoringServiceClient.create_model_monitoring_job",  # noqa: E501
    return_value=mock_created_monitoring_job,
)
def test_falls_back_to_table_uri_when_endpoint_id_missing(
    create_monitoring_job, preview_sdk_mocks
):
    _call_run(endpoint_id="")

    create_monitoring_job.assert_called_once()
    preview_sdk_mocks.MonitoringInput.assert_any_call(
        table_uri=TARGET_BQ_URI,
        timestamp_field="logging_time",
        window="1h",
    )


@mock.patch(
    "google.cloud.aiplatform_v1beta1.services.model_monitoring_service.ModelMonitoringServiceClient.create_model_monitoring_job",  # noqa: E501
)
def test_raises_when_training_uri_missing(create_monitoring_job, preview_sdk_mocks):
    with pytest.raises(ValueError, match="training_dataset_gcs_uri"):
        _call_run(training_dataset_gcs_uri="")

    create_monitoring_job.assert_not_called()


@mock.patch(
    "google.cloud.aiplatform_v1beta1.services.model_monitoring_service.ModelMonitoringServiceClient.create_model_monitoring_job",  # noqa: E501
)
def test_raises_when_logging_table_missing_even_with_endpoint(
    create_monitoring_job, preview_sdk_mocks
):
    with pytest.raises(ValueError, match="target_bq_table_uri"):
        _call_run(target_bq_table_uri="")

    create_monitoring_job.assert_not_called()


@mock.patch(
    "google.cloud.aiplatform_v1beta1.services.model_monitoring_service.ModelMonitoringServiceClient.create_model_monitoring_job",  # noqa: E501
)
def test_raises_when_target_missing(create_monitoring_job, preview_sdk_mocks):
    with pytest.raises(ValueError, match="target_bq_table_uri"):
        _call_run(endpoint_id="", target_bq_table_uri="")

    create_monitoring_job.assert_not_called()


@mock.patch(
    "google.cloud.aiplatform_v1beta1.services.model_monitoring_service.ModelMonitoringServiceClient.create_model_monitoring_job",  # noqa: E501
)
def test_raises_when_monitored_features_empty(
    create_monitoring_job, preview_sdk_mocks
):
    with pytest.raises(ValueError, match="monitored_features"):
        _call_run(monitored_features={})

    create_monitoring_job.assert_not_called()
