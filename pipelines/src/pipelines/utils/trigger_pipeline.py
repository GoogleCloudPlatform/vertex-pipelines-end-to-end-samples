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

from pipelines.utils.load_config import load_variables


def delete_previous_schedules(
    schedule_pipeline_name: str, project_id: str, location: str
):
    """
    Deletes all previous schedules matching the given display name.
    Ensures only one schedule exists per pipeline type.
    """
    all_schedules = aiplatform.PipelineJobSchedule.list(
        project=project_id,
        location=location,
    )
    for scheduled_job in all_schedules:
        print(f"Checking schedule: {scheduled_job.display_name}")
        if schedule_pipeline_name == scheduled_job.display_name:
            print(f"Deleting schedule: {scheduled_job.display_name}")
            scheduled_job.delete()


def _handle_schedule(
    display_name: str,
    scheduler_config: dict,
    pl: aiplatform.PipelineJob,
    project_id: str,
    location: str,
    service_account: str,
    network: str,
    pipeline_root: str,
    template_path: str,
    encryption_spec_key_name: str,
):
    """Create or delete a schedule for the given pipeline type."""
    if display_name == "training":
        schedule_name = "training_pipeline"
        enabled = scheduler_config.get("enable_training_scheduler") is True
        cron = scheduler_config.get("training_cron")
        max_concurrent = scheduler_config.get(
            "training_max_concurrent_run_count", 1
        )
        max_runs = scheduler_config.get("training_max_run_count", 0)
    else:
        schedule_name = "prediction_pipeline"
        enabled = scheduler_config.get("enable_prediction_scheduler") is True
        cron = scheduler_config.get("prediction_cron")
        max_concurrent = scheduler_config.get(
            "prediction_max_concurrent_run_count", 1
        )
        max_runs = scheduler_config.get("prediction_max_run_count", 0)

    if enabled and cron:
        delete_previous_schedules(schedule_name, project_id, location)

        scheduled_pl = aiplatform.PipelineJob(
            project=project_id,
            location=location,
            display_name=display_name,
            enable_caching=False,
            template_path=template_path,
            pipeline_root=pipeline_root,
            encryption_spec_key_name=encryption_spec_key_name,
        )

        print(f"Creating {display_name} pipeline schedule (caching disabled)")
        scheduled_pl.create_schedule(
            display_name=schedule_name,
            cron=cron,
            max_concurrent_run_count=max_concurrent,
            max_run_count=max_runs if max_runs != 0 else None,
            service_account=service_account,
            network=network,
        )
        print(f"Successfully created {display_name} pipeline schedule")
    else:
        print(
            f"{display_name.capitalize()} scheduler disabled, "
            "removing any existing schedules"
        )
        delete_previous_schedules(schedule_name, project_id, location)


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

    env_vars = load_variables()
    scheduler_config = env_vars.get("scheduler", {}) if env_vars else {}

    if scheduler_config and display_name in ("training", "prediction"):
        _handle_schedule(
            display_name,
            scheduler_config,
            pl,
            project_id,
            location,
            service_account,
            network,
            pipeline_root,
            template_path,
            encryption_spec_key_name,
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

    if args.wait == "true":
        wait = True
    elif args.wait == "false":
        wait = False
    else:
        raise ValueError("wait variable must be 'true' or 'false'")

    trigger_pipeline(
        template_path=args.template_path,
        display_name=args.display_name,
        wait=wait,
    )
