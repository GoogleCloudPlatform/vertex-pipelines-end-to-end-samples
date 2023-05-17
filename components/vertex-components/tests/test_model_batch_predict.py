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
import json
import pytest
from unittest.mock import Mock, patch
from kfp.v2.dsl import Model
from google.cloud.aiplatform_v1beta1.types.job_state import JobState


import vertex_components

model_batch_predict = vertex_components.model_batch_predict.python_func


SKEW_THRESHOLD = {"defaultSkewThreshold": {"value": 0.001}}
TRAIN_DATASET = {
    "gcsSource": {"uris": ["gs://file.csv"]},
    "dataFormat": "csv",
    "targetField": "col",
}


@pytest.mark.parametrize(
    (
        "source_format,destination_format,source_uri,monitoring_training_dataset,"
        "monitoring_alert_email_addresses,monitoring_skew_config"
    ),
    [
        ("bigquery", "bigquery", "bq://a.b.c", None, None, None),
        ("csv", "csv", '["gs://file.csv"]', None, None, None),
        ("csv", "csv", '["gs://file.csv"]', TRAIN_DATASET, [], SKEW_THRESHOLD),
        ("csv", "csv", '["gs://file.csv"]', TRAIN_DATASET, ["a@b.com"], SKEW_THRESHOLD),
    ],
)
def test_model_batch_predict(
    tmpdir,
    source_format,
    destination_format,
    source_uri,
    monitoring_training_dataset,
    monitoring_alert_email_addresses,
    monitoring_skew_config,
):
    """
    Asserts model_batch_predict successfully creates requests given different arguments.
    """
    mock_resource_name = "mock-batch-job"

    mock_job1 = Mock()
    mock_job1.name = mock_resource_name
    mock_job1.state = JobState.JOB_STATE_SUCCEEDED

    mock_model = Model(uri=tmpdir, metadata={"resourceName": ""})

    with patch(
        "google.cloud.aiplatform_v1beta1.services.job_service.JobServiceClient.create_batch_prediction_job",  # noqa: E501
        return_value=mock_job1,
    ) as create_job, patch(
        "google.cloud.aiplatform_v1beta1.services.job_service.JobServiceClient.get_batch_prediction_job",  # noqa: E501
        return_value=mock_job1,
    ) as get_job:
        (gcp_resources,) = model_batch_predict(
            model=mock_model,
            job_display_name="",
            project_location="",
            project_id="",
            source_uri=source_uri,
            destination_uri=destination_format,
            source_format=source_format,
            destination_format=destination_format,
            monitoring_training_dataset=monitoring_training_dataset,
            monitoring_alert_email_addresses=monitoring_alert_email_addresses,
            monitoring_skew_config=monitoring_skew_config,
        )

    create_job.assert_called_once()
    get_job.assert_called_once()
    assert (
        json.loads(gcp_resources)["resources"][0]["resourceUri"] == mock_resource_name
    )
