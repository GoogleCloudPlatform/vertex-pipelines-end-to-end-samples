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

import argparse
import os
from google.cloud import aiplatform


def trigger_pipeline(
    template_path: str,
    display_name: str,
    wait: bool = False,
) -> aiplatform.PipelineJob:
    """Trigger a Vertex Pipeline run from a (local) compiled pipeline definition.

    Args:
        template_path (str): file path to the compiled YAML pipeline
        display_name (str): Display name to use for the PipelineJob
        wait (bool): Wait for the pipeline to finish running

    Returns:
        aiplatform.PipelineJob: the Vertex PipelineJob object
    """
    project_id = os.environ["VERTEX_PROJECT_ID"]
    location = os.environ["VERTEX_LOCATION"]
    pipeline_root = os.environ["VERTEX_PIPELINE_ROOT"]
    service_account = os.environ["VERTEX_SA_EMAIL"]

    enable_caching = os.environ.get("ENABLE_PIPELINE_CACHING")
    if enable_caching is not None:
        true_ = ["1", "true"]
        false_ = ["0", "false"]
        if enable_caching.lower() not in true_ + false_:
            raise ValueError(
                "ENABLE_PIPELINE_CACHING env variable must be "
                "'true', 'false', '1' or '0', or not set."
            )
        enable_caching = enable_caching.lower() in true_

    # For below options, we want an empty string to become None, so we add "or None"
    encryption_spec_key_name = os.environ.get("VERTEX_CMEK_IDENTIFIER") or None
    network = os.environ.get("VERTEX_NETWORK") or None

    # Instantiate PipelineJob object
    pl = aiplatform.PipelineJob(
        project=project_id,
        location=location,
        display_name=display_name,
        enable_caching=enable_caching,
        template_path=template_path,
        pipeline_root=pipeline_root,
        encryption_spec_key_name=encryption_spec_key_name,
    )

    # Execute pipeline in Vertex
    pl.submit(
        service_account=service_account,
        network=network,
    )

    if wait:
        # Wait for pipeline to finish running before returning
        pl.wait()

    return pl


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--template_path",
        help="Path to the compiled pipeline (YAML)",
        type=str,
    )
    parser.add_argument(
        "--display_name",
        help="Display name for the PipelineJob",
        type=str,
    )

    parser.add_argument(
        "--wait",
        help="Wait for the pipeline to finish running",
        type=str,
    )
    # Get commandline args
    args = parser.parse_args()

    if args.wait.lower() == "true":
        wait = True
    elif args.wait.lower() != "false":
        raise ValueError("wait variable must be 'true' or 'false'")
    wait = False

    trigger_pipeline(
        template_path=args.template_path,
        display_name=args.display_name,
        wait=wait,
    )
