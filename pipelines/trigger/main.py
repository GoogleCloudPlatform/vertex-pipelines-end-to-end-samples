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

import argparse
import base64
import json
import logging
import os
import distutils.util
from typing import Optional, List

from google.cloud import aiplatform


def cf_handler(event, context) -> aiplatform.PipelineJob:
    """Handle the Pub/Sub message and make the call to trigger_pipeline_from_payload()
    to trigger the ML pipeline on Vertex. Returns the PipelineJob object.

    Args:
         event (dict):  The dictionary with data specific to this type of
                        event. The `@type` field maps to
                         `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
                        The `data` field maps to the PubsubMessage data
                        in a base64-encoded string. The `attributes` field maps
                        to the PubsubMessage attributes if any is present.
         context (google.cloud.functions.Context): Metadata of triggering event
                        including `event_id` which maps to the PubsubMessage
                        messageId, `timestamp` which maps to the PubsubMessage
                        publishTime, `event_type` which maps to
                        `google.pubsub.topic.publish`, and `resource` which is
                        a dictionary that describes the service API endpoint
                        pubsub.googleapis.com, the triggering topic's name, and
                        the triggering event type
                        `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
    Returns:
        aiplatform.PipelineJob
    """

    # take event["data"], base64-decode it and JSON decode to dict
    event["data"] = base64.b64decode(event["data"]).decode("utf-8")
    event["data"] = json.loads(event["data"])

    return trigger_pipeline_from_payload(event)


def trigger_pipeline_from_payload(payload: dict) -> aiplatform.PipelineJob:
    """Triggers a pipeline run from a payload dict, JSON pipeline definition,
    and env variables.
    Args:
        payload (dict): payload containing attributes and data.
        template_path (str): File path (local or GCS) of compiled pipeline definition.
    """

    payload = convert_payload(payload)
    env = get_env()

    return trigger_pipeline(
        project_id=env["project_id"],
        location=env["location"],
        template_path=payload["attributes"]["template_path"],
        parameter_values=payload["data"],
        pipeline_root=env["pipeline_root"],
        service_account=env["service_account"],
        encryption_spec_key_name=env["encryption_spec_key_name"],
        network=env["network"],
        enable_caching=payload["attributes"]["enable_caching"],
    )


def trigger_pipeline(
    project_id: str,
    location: str,
    template_path: str,
    pipeline_root: str,
    service_account: str,
    parameter_values: dict = {},
    encryption_spec_key_name: Optional[str] = None,
    network: Optional[str] = None,
    enable_caching: Optional[bool] = None,
) -> aiplatform.PipelineJob:
    """Trigger the Vertex Pipeline run.
    Args:
        project_id (str): GCP Project ID in which to run the Vertex Pipeline
        location (str): GCP region in which to run the Vertex Pipeline
        template_path (str): local or GCS path containing the (JSON) KFP
        pipeline definition
        pipeline_root (str): GCS path to use as the pipeline root (for passing
         metadata/artifacts within the pipeline)
        parameter_values (dict): dictionary containing the input parameters
        for the KFP pipeline
        service_account (str): email address of the service account that
        should be used to execute the ML pipeline in Vertex
        encryption_spec_key_name (Optional[str]): Cloud KMS resource ID
        of the customer managed encryption key (CMEK) that will protect the job
        network (Optional[str]): name of Compute Engine network to
        which the job should be visible
        enable_caching (Optional[bool]): Whether to enable caching of pipeline
        component results if component+inputs are the same. Defaults to None
        (enable caching, except where disabled at a component level)
    """

    # Initialise API client
    aiplatform.init(project=project_id, location=location)

    # Instantiate PipelineJob object
    pl = aiplatform.pipeline_jobs.PipelineJob(
        # Display name is required but seemingly not used
        # see
        # https://github.com/googleapis/python-aiplatform/blob/9dcf6fb0bc8144d819938a97edf4339fe6f2e1e6/google/cloud/aiplatform/pipeline_jobs.py#L260 # noqa
        display_name=template_path,
        enable_caching=enable_caching,
        template_path=template_path,
        parameter_values=parameter_values,
        pipeline_root=pipeline_root,
        encryption_spec_key_name=encryption_spec_key_name,
    )

    # Execute pipeline in Vertex
    pl.submit(
        service_account=service_account,
        network=network,
    )

    return pl


def convert_payload(payload: dict) -> dict:
    """
    Processes the payload dictionary.
    Converts enable_caching and adds their defaults if they are missing.

    Args:
        payload (dict): Cloud Function event payload,
        or the contents of a payload JSON file
    """

    # make a copy of the payload so we are not modifying the original
    payload = payload.copy()

    # if payload["data"] is missing, add it as empty dict
    payload["data"] = payload.get("data", {})

    # if enable_caching value is present and not None, convert from str to bool
    # otherwise, it needs to be None
    if payload["attributes"].get("enable_caching") is not None:
        payload["attributes"]["enable_caching"] = bool(
            distutils.util.strtobool(payload["attributes"]["enable_caching"])
        )
    else:
        payload["attributes"]["enable_caching"] = None

    return payload


def get_env() -> dict:
    """Get the necessary environment variables for pipeline runs,
    and return them as a dictionary.
    """

    project_id = os.environ["VERTEX_PROJECT_ID"]
    location = os.environ["VERTEX_LOCATION"]
    pipeline_root = os.environ["VERTEX_PIPELINE_ROOT"]
    service_account = os.environ["VERTEX_SA_EMAIL"]
    # For CMEK and network, we want an empty string to become None, so we add "or None"
    encryption_spec_key_name = os.environ.get("VERTEX_CMEK_IDENTIFIER") or None
    network = os.environ.get("VERTEX_NETWORK") or None

    return {
        "project_id": project_id,
        "location": location,
        "pipeline_root": pipeline_root,
        "service_account": service_account,
        "encryption_spec_key_name": encryption_spec_key_name,
        "network": network,
    }


def sandbox_run(args: List[str] = None) -> aiplatform.PipelineJob:
    """Trigger a Vertex Pipeline run from a (local) compiled pipeline definition.
    Returns the PipelineJob object of the triggered pipeline run.
    Usage: python main.py --template_path=pipeline.json --enable_caching=true
    """
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--template_path", help="Path to the compiled pipeline (JSON)", type=str
    )
    parser.add_argument("--enable_caching", type=str, default=None)

    # Get commandline args
    args = parser.parse_args(args)

    # If empty value for enable_caching provided on commandline default to None
    if args.enable_caching == "":
        args.enable_caching = None

    payload = {
        "attributes": {
            "template_path": args.template_path,
            "enable_caching": args.enable_caching,
        }
        # "data" omitted as pipeline params are taken from the default args
        # in compiled JSON pipeline
    }

    return trigger_pipeline_from_payload(payload)


if __name__ == "__main__":
    sandbox_run()
