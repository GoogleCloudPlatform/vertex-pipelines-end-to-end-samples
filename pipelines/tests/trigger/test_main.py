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

from unittest import mock
import pytest
import base64
import json
import os

from pipelines.trigger.main import cf_handler, convert_payload, get_env


def test_cf_handler():

    test_parameter_values = {"key1": "val1", "key2": "val2"}

    encoded_param_values = str(
        base64.b64encode(json.dumps(test_parameter_values).encode("utf-8")), "utf-8"
    )

    payload = {
        "attributes": {"template_path": "gs://my-bucket/my-template-path.json"},
        "data": encoded_param_values,
    }

    with mock.patch(
        "pipelines.trigger.main.trigger_pipeline_from_payload"
    ) as mock_trigger_pipeline_from_payload:

        cf_handler(payload, {})

        mock_trigger_pipeline_from_payload.assert_called_with(
            payload,
        )


def test_trigger_pipeline():

    project_id = "my-test-project"
    location = "europe-west4"
    template_path = "gs://my-bucket/pipeline.json"
    parameter_values = {"key1": "val1", "key2": "val2"}
    pipeline_root = "gs://my-bucket/pipeline_root"
    service_account = "my_service_account@my-test-project.iam.gserviceaccount.com"
    encryption_spec_key_name = "my-cmek"
    network = "my-network"
    enable_caching = True

    with mock.patch("pipelines.trigger.main.aiplatform") as mock_aiplatform:

        from pipelines.trigger.main import trigger_pipeline

        pl = trigger_pipeline(
            project_id=project_id,
            location=location,
            template_path=template_path,
            parameter_values=parameter_values,
            pipeline_root=pipeline_root,
            service_account=service_account,
            encryption_spec_key_name=encryption_spec_key_name,
            network=network,
            enable_caching=enable_caching,
        )

        mock_aiplatform.init.assert_called_with(project=project_id, location=location)

        mock_aiplatform.pipeline_jobs.PipelineJob.assert_called_with(
            display_name=template_path,
            enable_caching=enable_caching,
            template_path=template_path,
            parameter_values=parameter_values,
            pipeline_root=pipeline_root,
            encryption_spec_key_name=encryption_spec_key_name,
        )

        pl.submit.assert_called_with(
            service_account=service_account,
            network=network,
        )


@pytest.mark.parametrize(
    "env_vars,test_input,expected",
    [
        # enable_caching
        (
            {},
            {"attributes": {"template_path": "pipeline.json"}},
            {
                "attributes": {
                    "template_path": "pipeline.json",
                    "enable_caching": None,
                },
                "data": {},
            },
        ),
        # enable_caching true
        (
            {},
            {
                "attributes": {
                    "template_path": "pipeline.json",
                    "enable_caching": "true",
                }
            },
            {
                "attributes": {
                    "template_path": "pipeline.json",
                    "enable_caching": True,
                },
                "data": {},
            },
        ),
    ],
)
def test_convert_payload(env_vars, test_input, expected):

    with mock.patch.dict(os.environ, env_vars, clear=True):
        assert convert_payload(test_input) == expected


@pytest.mark.parametrize(
    "env_vars,expected",
    [
        # encryption_spec_key_name and network present
        (
            {
                "VERTEX_PROJECT_ID": "my-project-id",
                "VERTEX_LOCATION": "europe-west4",
                "VERTEX_PIPELINE_ROOT": "gs://my-pipeline-root/folder",
                "VERTEX_SA_EMAIL": "my-sa@my-project-id.iam.gserviceaccount.com",
                "VERTEX_CMEK_IDENTIFIER": "my-cmek",
                "VERTEX_NETWORK": "my-network",
            },
            {
                "project_id": "my-project-id",
                "location": "europe-west4",
                "pipeline_root": "gs://my-pipeline-root/folder",
                "service_account": "my-sa@my-project-id.iam.gserviceaccount.com",
                "encryption_spec_key_name": "my-cmek",
                "network": "my-network",
            },
        ),
        # encryption_spec_key_name and network are empty string
        (
            {
                "VERTEX_PROJECT_ID": "my-project-id",
                "VERTEX_LOCATION": "europe-west4",
                "VERTEX_PIPELINE_ROOT": "gs://my-pipeline-root/folder",
                "VERTEX_SA_EMAIL": "my-sa@my-project-id.iam.gserviceaccount.com",
                "VERTEX_CMEK_IDENTIFIER": "",
                "VERTEX_NETWORK": "",
            },
            {
                "project_id": "my-project-id",
                "location": "europe-west4",
                "pipeline_root": "gs://my-pipeline-root/folder",
                "service_account": "my-sa@my-project-id.iam.gserviceaccount.com",
                "encryption_spec_key_name": None,
                "network": None,
            },
        ),
        # encryption_spec_key_name and network absent
        (
            {
                "VERTEX_PROJECT_ID": "my-project-id",
                "VERTEX_LOCATION": "europe-west4",
                "VERTEX_PIPELINE_ROOT": "gs://my-pipeline-root/folder",
                "VERTEX_SA_EMAIL": "my-sa@my-project-id.iam.gserviceaccount.com",
            },
            {
                "project_id": "my-project-id",
                "location": "europe-west4",
                "pipeline_root": "gs://my-pipeline-root/folder",
                "service_account": "my-sa@my-project-id.iam.gserviceaccount.com",
                "encryption_spec_key_name": None,
                "network": None,
            },
        ),
    ],
)
def test_get_env(env_vars, expected, monkeypatch):

    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)

    env = get_env()

    assert env == expected


@pytest.mark.parametrize(
    "cmdline_args,expected_payload",
    [
        (
            [
                "--template_path=pipeline.json",
                "--enable_caching=True",
            ],
            {
                "attributes": {
                    "template_path": "pipeline.json",
                    "enable_caching": "True",
                },
            },
        ),
        # enable_caching omitted on commandline
        (
            [
                "--template_path=pipeline.json",
                "--enable_caching=",
            ],
            {
                "attributes": {
                    "template_path": "pipeline.json",
                    "enable_caching": None,
                },
            },
        ),
    ],
)
def test_sandbox_run(cmdline_args, expected_payload):

    # mock get_args(), and trigger_pipeline_from_payload()
    with mock.patch(
        "pipelines.trigger.main.trigger_pipeline_from_payload"
    ) as mock_trigger_pipeline_from_payload:

        from pipelines.trigger.main import sandbox_run

        sandbox_run(cmdline_args)

        mock_trigger_pipeline_from_payload.assert_called_once_with(expected_payload)
