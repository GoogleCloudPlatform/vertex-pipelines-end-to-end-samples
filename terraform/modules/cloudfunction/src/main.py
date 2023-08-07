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

import base64
import json
import os
from distutils.util import strtobool
from google.cloud import aiplatform


def cf_handler(event, context):
    """Background Cloud Function to be triggered by Pub/Sub.
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
        None. The output is written to Cloud Logging.
    """

    payload = json.loads(base64.b64decode(event["data"]).decode("utf-8"))

    project_id = os.environ["VERTEX_PROJECT_ID"]
    location = os.environ["VERTEX_LOCATION"]
    pipeline_root = os.environ["VERTEX_PIPELINE_ROOT"]
    service_account = os.environ["VERTEX_SA_EMAIL"]

    template_path = payload["template_path"]
    display_name = payload["display_name"]
    pipeline_parameters = payload.get("pipeline_parameters")
    enable_caching = payload.get("enable_pipeline_caching")
    if enable_caching:
        enable_caching = bool(strtobool(enable_caching))

    # For below options, we want an empty string to become None, so we add "or None"
    encryption_spec_key_name = os.environ.get("VERTEX_CMEK_IDENTIFIER") or None
    network = os.environ.get("VERTEX_NETWORK") or None

    # Instantiate PipelineJob object
    pl = aiplatform.pipeline_jobs.PipelineJob(
        project=project_id,
        location=location,
        display_name=display_name,
        enable_caching=enable_caching,
        template_path=template_path,
        parameter_values=pipeline_parameters,
        pipeline_root=pipeline_root,
        encryption_spec_key_name=encryption_spec_key_name,
    )

    # Execute pipeline in Vertex
    pl.submit(
        service_account=service_account,
        network=network,
    )
