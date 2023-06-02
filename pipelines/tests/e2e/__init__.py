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

import logging
from typing import Callable

import pytest
import os
from google.cloud import storage
from kfp.v2 import compiler

from pipelines.trigger.main import trigger_pipeline_from_payload

project_id = os.environ["VERTEX_PROJECT_ID"]
project_location = os.environ["VERTEX_LOCATION"]


def split_output_uri(output_uri: str):
    """
    Splits an output uri into its bucket name and blob path
    Args: output_uri: (str) The output uri to split
    Returns: A tuple of (bucket_name, blob_path)
    """
    output_uri_noprefix = output_uri[5:]  # remove the gs://
    output_uri_noprefix_split = output_uri_noprefix.split("/")
    bucket_name = output_uri_noprefix_split[0]
    blob_path = "/".join(output_uri_noprefix_split[1:])
    return (bucket_name, blob_path)


def check_gcs_uri(output_uri: str, storage_client):
    """
    Tests whether a uri exists on GCS. If not, check whether it is a folder path.
    Args:
        output_uri: (str) The output_uri to test existence of
        storage_client: (GCS client object) The GCS client for the project
    Returns: (int)
        None if the output_uri is not a file or a folder and therefore does not exist,
        The uri's size otherwise (folder size if it is a folder)
    """
    bucket_name, blob_path = split_output_uri(output_uri)
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_path)
    # If not a file, assume its a folder and sum the size of the blobs inside it
    if not blob:
        # All files in the folder would have a prefix of the folder path
        blob_contents = storage_client.list_blobs(bucket_name, prefix=blob_path)
        if not blob_contents:
            return None
        else:
            folder_size = 0
            for blob in blob_contents:
                folder_size += blob.size
            return folder_size
    return blob.size


def check_vertex_model_uri(
    model_id: str,
    model_location: str,
) -> bool:
    """
    Tests whether model artifact exist in Vertex AI.

    Args:
        model_id (str): Vertex model id
        model_location (str) : Vertex model location

    Returns:
        bool: True, if the model exists in Vertex AI.
             Otherwises, False
    """
    from google.cloud.aiplatform import Model

    try:
        Model(
            model_name=model_id,
            project=project_id,
            location=model_location,
        )
        return True
    except Exception:
        return False


def check_vertex_endpoint_uri(
    endpoint_id: str,
    endpoint_location: str,
) -> bool:
    """
    Tests whether endpoint artifact exist in Vertex AI.

    Args:
        endpoint_id (str): Vertex endpoint id
        endpoint_location (str) : Vertex endpoint location

    Returns:
        bool: True, if the endpoint exists in Vertex AI.
             Otherwises, False
    """
    from google.cloud.aiplatform import Endpoint

    try:
        Endpoint(
            endpoint_name=endpoint_id,
            project=project_id,
            location=endpoint_location,
        )
        return True
    except Exception:
        return False


def check_batch_prediction_job_uri(
    job_id: str,
    job_location: str,
) -> bool:
    """
    Tests whether endpoint artifact exist in Vertex AI.

    Args:
       job_id (str): Vertex batch prediction job id
       job_location (str) : Vertex batch prediction  location

    Returns:
        bool: True, if the prediction job exists in Vertex AI.
             Otherwises, False
    """
    from google.cloud.aiplatform import BatchPredictionJob

    try:
        BatchPredictionJob(
            batch_prediction_job_name=job_id,
            project=project_id,
            location=job_location,
        )
        return True
    except Exception:
        return False


def pipeline_e2e_test(
    pipeline_func: Callable,
    common_tasks: dict,
    enable_caching: bool,
    **kwargs: dict,
):
    """
    Test pipeline e2e for all expected tasks
    1. Check all expected tasks occured in the pipeline
    2. Check if these tasks output the correct artifacts and they are all accessible

    Args:
        pipeline_func (Callable): KFP pipeline function to test
        enable_caching (bool): enable pipeline caching
        common_tasks (dict): tasks in pipline that are executed everytime
        **kwargs (dict): conditional tasks groups in dictionary
    """

    pipeline_json = f"{pipeline_func.__name__}.json"

    compiler.Compiler().compile(
        pipeline_func=pipeline_func,
        package_path=pipeline_json,
        type_check=False,
    )

    payload = {
        "attributes": {
            "template_path": pipeline_json,
            "enable_caching": str(enable_caching),
        }
    }

    pl = trigger_pipeline_from_payload(payload)
    pl.wait()

    # Tests
    # 1. Check all expected tasks occured in the pipeline
    # 2-1. Check if these tasks output the correct artifacts
    # 2-2. Check if these artifacts are accessible
    details = pl.to_dict()
    tasks = details["jobDetail"]["taskDetails"]

    # check common tasks
    if len(common_tasks):
        check_pipeline_tasks(
            tasks=tasks,
            expected_tasks=common_tasks,
            allow_tasks_missing=False,
        )

    # check conditional tasks
    for _, conditional_tasks in kwargs.items():
        check_pipeline_tasks(
            tasks=tasks,
            expected_tasks=conditional_tasks,
            allow_tasks_missing=True,
        )


def check_pipeline_tasks(tasks: list, expected_tasks: dict, allow_tasks_missing: bool):
    """
    Test if expected_task meets all the requirements:
    1. if expected tasks occured in the pipeline
    2. if these tasks output the correct artifacts

    Args:
        tasks (list): all pipeline tasks
        expected_tasks (dict): tasks for check
        allow_tasks_missing (bool): if missing tasks in one task group is allowed
            Only allow missing tasks in conditional task groups as sometimes they are
            not executed.
    """
    # Tests

    actual_tasks_expected = {
        # Create a dict key for a task, where the corresponding value is another dict
        # This corresponding dict will contain output_names and their output_uri
        task["taskName"]: {
            # Create a key/value pair of output_name and output_uri
            # Do this for every output name
            output_name: output_dict["artifacts"][0]["uri"]
            if output_dict["artifacts"][0].get("uri") is not None
            else None
            for output_name, output_dict in task.get("outputs", {}).items()
        }
        # Create the above task dictionary for each task in the pipeline's tasks
        # But only if the task is in expected tasks
        for task in tasks
        if task["taskName"] in list(expected_tasks.keys())
    }

    # 1. Missing task check
    # If all of tasks in a group are not executed,
    # the remaining check logic will be skipped.
    # Otherwise, it will check if there are missing tasks.
    if (len(actual_tasks_expected) == 0) and allow_tasks_missing:
        logging.info(f"task: {expected_tasks} are not executed")
        return None
    else:
        missing_tasks = [
            task_name
            for task_name in expected_tasks.keys()
            if task_name not in actual_tasks_expected.keys()
        ]
        assert len(missing_tasks) == 0, f"expected but missing tasks: {missing_tasks}"

    # test functions mappiing
    test_functions = {
        "models": check_vertex_model_uri,
        "endpoints": check_vertex_endpoint_uri,
        "batchPredictionJobs": check_batch_prediction_job_uri,
    }

    # initialise GCS client for the project
    storage_client = storage.Client(project=project_id)

    # 2. Outputs check
    for task_name, expected_output in expected_tasks.items():
        actual_outputs = actual_tasks_expected[task_name]
        # 2-1. if the output artifact are as expected
        diff = set(expected_output).symmetric_difference(actual_outputs.keys())
        assert (
            len(diff) == 0
        ), f"task: {task_name}, \
            expected_output {expected_output}, \
            actual_outputs: {actual_outputs.keys()}"
        for output_artifact in expected_output:
            output_uri = actual_outputs[output_artifact]

            # 2-2. if output is generated successfully
            # if there is no output uri, skip
            if output_uri is None:
                continue
            # if the output uri is a gcs path, fetch the file
            elif output_uri.startswith("gs://"):
                file_size = check_gcs_uri(output_uri, storage_client)
                assert (
                    file_size > 0
                ), f"{output_artifact} in task {task_name} is not accessible"
            # for Vertex resource check if the resource exists
            else:
                # all Vertex AI resource uri following this pattern:
                # ‘projects/<my-project>/locations/<location>/<resource_type>/<resource_name>’
                artifact_type = output_uri.split("/")[-2]
                object_existence = test_functions[artifact_type](
                    output_uri.split("/")[-1],  # id
                    output_uri.split("/")[-3],  # location
                )
                assert (
                    object_existence
                ), f"{output_artifact} in task {task_name} is not accessible \
                    with {output_uri.split('/')[-1]}"
