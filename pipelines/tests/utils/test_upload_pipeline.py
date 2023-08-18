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

from unittest import mock
import pytest
from pipelines.utils.upload_pipeline import main, upload_pipeline


@pytest.mark.parametrize(
    "input_tags",
    # test for different combinations of AR tags to use
    # when uploading the compiled pipeline to Artifact Registry
    [
        None,  # no tag
        ["dummy_tag1"],  # single tag
        ["dummy_tag1", "dummy_tag2"],  # multiple tags
    ],
)
@mock.patch("pipelines.utils.upload_pipeline.upload_pipeline")
def test_main(mock_upload_pipeline, input_tags):
    yaml = "path/to/template.yaml"
    dest = "https://europe-west1-kfp.pkg.dev/dummy-project/dummy-repo"

    args = [
        f"--dest={dest}",
        f"--yaml={yaml}",
    ]

    if input_tags:
        args.extend([f"--tag={tag}" for tag in input_tags])

    main(args)

    mock_upload_pipeline.assert_called_with(
        host=dest,
        file_name=yaml,
        tags=input_tags,
    )


@mock.patch("pipelines.utils.upload_pipeline.RegistryClient")
def test_upload_pipeline(mock_registry_client):

    yaml = "path/to/template.yaml"
    dest = "https://europe-west1-kfp.pkg.dev/dummy-project/dummy-repo"

    input_tags = ["dummy_tag1", "dummy_tag2"]

    upload_pipeline(
        host=dest,
        file_name=yaml,
        tags=input_tags,
    )

    mock_registry_client.assert_called_with(
        host=dest,
    )

    mock_registry_client.return_value.upload_pipeline.assert_called_with(
        file_name=yaml,
        tags=input_tags,
    )
