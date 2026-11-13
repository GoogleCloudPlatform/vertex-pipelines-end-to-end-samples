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

from kfp.dsl import Model
from unittest import mock
import pytest

import components

lookup_model = components.lookup_model.python_func


@mock.patch("google.cloud.aiplatform.Model")
def test_lookup_model(mock_model, tmp_path):
    """
    Assert lookup_model produces expected resource name, and that list method is
    called with the correct arguemnts
    """

    # Mock attribute and method
    mock_path = str(tmp_path / "model")
    mock_model.resource_name = "projects/p/locations/l/models/123"
    mock_model.uri = mock_path
    mock_model.version_id = "33"
    mock_model.list.return_value = [mock_model]

    found_model_resource_name, _, _ = lookup_model(
        model_name="my-model",
        location="europe-west4",
        project="my-project-id",
        fail_on_model_not_found=False,
        model=Model(uri=mock_path),
    )

    assert found_model_resource_name == "projects/p/locations/l/models/123@33"

    # Check the list method was called once with the correct arguments
    mock_model.list.assert_called_once_with(
        filter='display_name="my-model"',
        location="europe-west4",
        project="my-project-id",
    )


@mock.patch("google.cloud.aiplatform.Model")
def test_lookup_model_when_no_models(mock_model, tmp_path):
    """
    Checks that when there are no models and fail_on_model_found = False,
    lookup_model returns an empty string.
    """
    mock_model.list.return_value = []
    exported_model_resource_name, _, _ = lookup_model(
        model_name="my-model",
        location="europe-west4",
        project="my-project-id",
        fail_on_model_not_found=False,
        model=Model(uri=str(tmp_path / "model")),
    )

    assert exported_model_resource_name == ""


@mock.patch("google.cloud.aiplatform.Model")
def test_lookup_model_when_no_models_fail(mock_model, tmp_path):
    """
    Checks that when there are no models and fail_on_model_found = True,
    lookup_model raises a RuntimeError.
    """
    mock_model.list.return_value = []

    # Verify that a ValueError is raised
    with pytest.raises(RuntimeError):
        lookup_model(
            model_name="my-model",
            location="europe-west4",
            project="my-project-id",
            fail_on_model_not_found=True,
            model=Model(uri=str(tmp_path / "model")),
        )


@mock.patch("google.cloud.aiplatform.Model")
def test_lookup_model_extracts_training_dataset_gcs_uri(mock_model, tmp_path):
    """
    Checks that when the model's training_dataset.json metadata exists,
    lookup_model extracts the GCS URI for use as a Model Monitoring v2
    baseline dataset.
    """
    import json

    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "training_dataset.json").write_text(
        json.dumps(
            {
                "gcsSource": {"uris": ["gs://my-bucket/train.csv"]},
                "dataFormat": "csv",
                "targetField": "total_fare",
            }
        )
    )

    mock_model.resource_name = "my-model-resource-name"
    mock_model.uri = str(model_dir)
    mock_model.list.return_value = [mock_model]

    _, training_dataset, training_dataset_gcs_uri = lookup_model(
        model_name="my-model",
        location="europe-west4",
        project="my-project-id",
        fail_on_model_not_found=False,
        model=Model(uri=str(model_dir)),
    )

    assert training_dataset_gcs_uri == "gs://my-bucket/train.csv"
    assert training_dataset["gcsSource"]["uris"] == ["gs://my-bucket/train.csv"]


@mock.patch("google.cloud.aiplatform.Model")
def test_lookup_model_normalizes_gcs_fuse_path(mock_model, tmp_path):
    """
    Older training runs persisted the local Cloud Storage FUSE mount path
    (e.g. "/gcs/bucket/object") instead of a "gs://" URI in
    training_dataset.json. lookup_model must normalize this to a "gs://" URI,
    since Model Monitoring v2 rejects anything else.
    """
    import json

    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "training_dataset.json").write_text(
        json.dumps(
            {
                "gcsSource": {"uris": ["/gcs/my-bucket/path/to/train_data"]},
                "dataFormat": "csv",
                "targetField": "total_fare",
            }
        )
    )

    mock_model.resource_name = "my-model-resource-name"
    mock_model.uri = str(model_dir)
    mock_model.list.return_value = [mock_model]

    _, training_dataset, training_dataset_gcs_uri = lookup_model(
        model_name="my-model",
        location="europe-west4",
        project="my-project-id",
        fail_on_model_not_found=False,
        model=Model(uri=str(model_dir)),
    )

    assert training_dataset_gcs_uri == "gs://my-bucket/path/to/train_data"
    assert training_dataset["gcsSource"]["uris"] == [
        "gs://my-bucket/path/to/train_data"
    ]


@mock.patch("google.cloud.aiplatform.Model")
def test_lookup_model_when_training_dataset_metadata_missing(mock_model, tmp_path):
    """
    Checks that lookup_model returns an empty string (rather than raising) when
    the model has no training_dataset.json metadata.
    """
    mock_model.resource_name = "my-model-resource-name"
    mock_model.uri = str(tmp_path / "model")
    mock_model.list.return_value = [mock_model]

    _, training_dataset, training_dataset_gcs_uri = lookup_model(
        model_name="my-model",
        location="europe-west4",
        project="my-project-id",
        fail_on_model_not_found=False,
        model=Model(uri=str(tmp_path / "model")),
    )

    assert training_dataset_gcs_uri == ""
    assert training_dataset == {}
