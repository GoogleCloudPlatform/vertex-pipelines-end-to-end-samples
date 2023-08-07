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
import base64
import json

from src.main import cf_handler


@pytest.mark.parametrize(
    "test_enable_caching_input,enable_caching_expected",
    # test for different values of "enable_pipeline_caching" env var (left)
    # vs actual value passed to PipelineJob enable_caching (right)
    [
        ("True", True),
        ("true", True),
        ("False", False),
        ("false", False),
        (None, None),  # enable_pipeline_caching env var not set
    ],
)
@mock.patch("google.cloud.aiplatform.pipeline_jobs.PipelineJob")
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

    payload = {
        "template_path": template_path,
        "display_name": display_name,
        "pipeline_parameters": {
            "foo": "bar",
            "abc": 123,
        },
    }

    if enable_caching is not None:
        payload["enable_pipeline_caching"] = enable_caching

    # encode as base64 to feed into Cloud Function
    event = {"data": base64.b64encode(json.dumps(payload).encode("utf-8"))}

    env_vars = {
        "VERTEX_PROJECT_ID": project_id,
        "VERTEX_LOCATION": region,
        "VERTEX_SA_EMAIL": service_account,
        "VERTEX_NETWORK": network,
        "VERTEX_CMEK_IDENTIFIER": encryption_spec_key_name,
        "VERTEX_PIPELINE_ROOT": pipeline_root,
    }

    with mock.patch.dict(os.environ, env_vars):

        cf_handler(event, None)

        mock_pipelinejob.assert_called_with(
            project=project_id,
            location=region,
            display_name=display_name,
            enable_caching=enable_caching_expected,
            template_path=template_path,
            pipeline_root=pipeline_root,
            encryption_spec_key_name=encryption_spec_key_name,
            parameter_values=payload["pipeline_parameters"],
        )

        mock_pipelinejob.return_value.submit.assert_called_with(
            service_account=service_account,
            network=network,
        )
