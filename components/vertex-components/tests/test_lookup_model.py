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

import google.cloud.aiplatform  # noqa
from kfp.v2.dsl import Model
from unittest import mock
import pytest

import vertex_components

lookup_model = vertex_components.lookup_model.python_func


def test_lookup_model(tmpdir):
    """
    Assert lookup_model produces expected resource name, and that list method is
    called with the correct arguemnts

    Args:
        tmpdir: built-in pytest tmpdir fixture

    Returns:
        None
    """
    with mock.patch("google.cloud.aiplatform.Model") as mock_model:

        # Mock attribute and method

        mock_path = tmpdir
        mock_model.resource_name = "my-model-resource-name"
        mock_model.uri = mock_path
        mock_model.list.return_value = [mock_model]

        # Invoke the model look up
        found_model_resource_name, _ = lookup_model(
            model_name="my-model",
            project_location="europe-west4",
            project_id="my-project-id",
            order_models_by="create_time desc",
            fail_on_model_not_found=False,
            model=Model(uri=mock_path),
        )

        assert found_model_resource_name == "my-model-resource-name"

        # Check the list method was called once with the correct arguments
        mock_model.list.assert_called_once_with(
            filter='display_name="my-model"',
            order_by="create_time desc",
            location="europe-west4",
            project="my-project-id",
        )


def test_lookup_model_when_no_models(tmpdir):
    """
    Checks that when there are no models and fail_on_model_found = False,
    lookup_model returns an empty string.

    Args:
        tmpdir: built-in pytest tmpdir fixture

    Returns:
        None
    """
    with mock.patch("google.cloud.aiplatform.Model") as mock_model:
        mock_model.list.return_value = []
        exported_model_resource_name, _ = lookup_model(
            model_name="my-model",
            project_location="europe-west4",
            project_id="my-project-id",
            order_models_by="create_time desc",
            fail_on_model_not_found=False,
            model=Model(uri=str(tmpdir)),
        )
    print(exported_model_resource_name)
    assert exported_model_resource_name == ""


def test_lookup_model_when_no_models_fail(tmpdir):
    """
    Checks that when there are no models and fail_on_model_found = True,
    lookup_model raises a RuntimeError.

    Args:
        tmpdir: built-in pytest tmpdir fixture

    Returns:
        None
    """
    with mock.patch("google.cloud.aiplatform.Model") as mock_model:
        mock_model.list.return_value = []

        # Verify that a ValueError is raised
        with pytest.raises(RuntimeError):
            lookup_model(
                model_name="my-model",
                project_location="europe-west4",
                project_id="my-project-id",
                order_models_by="create_time desc",
                fail_on_model_not_found=True,
                model=Model(uri=str(tmpdir)),
            )
