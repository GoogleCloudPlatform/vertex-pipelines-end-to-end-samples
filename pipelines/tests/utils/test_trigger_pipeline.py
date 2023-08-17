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
import os

from pipelines.utils.trigger_pipeline import trigger_pipeline


@pytest.mark.parametrize(
    "test_enable_caching_input,enable_caching_expected",
    # test for different values of "ENABLE_PIPELINE_CACHING" env var (left)
    # vs actual value passed to PipelineJob enable_caching (right)
    [
        ("True", True),
        ("true", True),
        ("False", False),
        ("false", False),
        ("1", True),
        ("0", False),
        (None, None),  # ENABLE_PIPELINE_CACHING env var not set
    ],
)
@mock.patch("google.cloud.aiplatform.PipelineJob")
def test_trigger_pipeline(
    mock_pipelinejob, test_enable_caching_input, enable_caching_expected
):

    template_path = "path/to/template.yaml"
    enable_caching = test_enable_caching_input
    pipeline_root = "gs://my-pipeline-root/abc123"
    encryption_spec_key_name = "dummy_encryption_spec_key_name"
    project_id = "dummy_project_id"
    region = "dummy_region"
    service_account = "dummy_sa@dummy_project_id.iam.gserviceaccount.com"
    network = "dummy_network"
    display_name = "my first pipeline"

    env_vars = {
        "VERTEX_PROJECT_ID": project_id,
        "VERTEX_LOCATION": region,
        "VERTEX_SA_EMAIL": service_account,
        "VERTEX_NETWORK": network,
        "VERTEX_CMEK_IDENTIFIER": encryption_spec_key_name,
        "VERTEX_PIPELINE_ROOT": pipeline_root,
    }

    if enable_caching is not None:
        env_vars["ENABLE_PIPELINE_CACHING"] = enable_caching

    with mock.patch.dict(os.environ, env_vars):

        trigger_pipeline(
            template_path=template_path,
            display_name=display_name,
        )

        mock_pipelinejob.assert_called_with(
            project=project_id,
            location=region,
            display_name=display_name,
            enable_caching=enable_caching_expected,
            template_path=template_path,
            pipeline_root=pipeline_root,
            encryption_spec_key_name=encryption_spec_key_name,
        )

        mock_pipelinejob.return_value.submit.assert_called_with(
            service_account=service_account,
            network=network,
        )


@mock.patch("google.cloud.aiplatform.PipelineJob")
def test_trigger_pipeline_invalid_caching_env_var(mock_pipelinejob):

    template_path = "path/to/template.yaml"
    enable_caching = "invalid_value"
    pipeline_root = "gs://my-pipeline-root/abc123"
    encryption_spec_key_name = "dummy_encryption_spec_key_name"
    project_id = "dummy_project_id"
    region = "dummy_region"
    service_account = "dummy_sa@dummy_project_id.iam.gserviceaccount.com"
    network = "dummy_network"
    display_name = "my first pipeline"

    env_vars = {
        "VERTEX_PROJECT_ID": project_id,
        "VERTEX_LOCATION": region,
        "VERTEX_SA_EMAIL": service_account,
        "VERTEX_NETWORK": network,
        "VERTEX_CMEK_IDENTIFIER": encryption_spec_key_name,
        "VERTEX_PIPELINE_ROOT": pipeline_root,
        "ENABLE_PIPELINE_CACHING": enable_caching,
    }

    with mock.patch.dict(os.environ, env_vars), pytest.raises(ValueError):

        trigger_pipeline(
            template_path=template_path,
            display_name=display_name,
        )
