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

from tests.e2e.test_e2e import pipeline_e2e_test


def test_pipeline_run(enable_caching) -> None:
    """
    Tests if pipeline is run successfully
    Triggers pipeline synchronously.
    Tests will fail if:
    - Any errors are thrown during execution
    - Any of the expected component outputs are empty (size == 0kb)

    Arguments:
        None

    Returns:
        None
    """

    pipeline_json = "training.json"

    # tasks (components) and outputs for tasks which occur unconditionally
    common_tasks = {
        "get-current-time": [],
        "bq-query-to-table": [],
        "bq-query-to-table-2": [],
        "bq-query-to-table-3": [],
        "bq-query-to-table-4": [],
        "bq-query-to-table-5": [],
        "extract-bq-to-dataset": ["dataset"],
        "extract-bq-to-dataset-2": ["dataset"],
        "extract-bq-to-dataset-3": ["dataset"],
        "generate-statistics": ["statistics"],
        "visualise-statistics": ["view"],
        "validate-schema": ["anomalies"],
        "show-anomalies": [],
        "train-tensorflow-model": ["model", "metrics_artifact"],
        "lookup-model": ["model"],
        "predict-tensorflow-model": ["predictions"],
        "calculate-eval-metrics": ["eval_metrics", "view"],
    }
    conditional_task_one = {
        "upload-model": [],
        "copy-artifact": ["des_artifact"],
    }

    condtional_task_two = {
        "export-model": ["model"],
        "predict-tensorflow-model-2": ["predictions"],
        "calculate-eval-metrics-2": ["eval_metrics", "view"],
        "compare-models": [],
    }

    conditional_task_three = {
        "upload-model-2": [],
        "copy-artifact-2": ["des_artifact"],
    }

    pipeline_e2e_test(
        template_path=pipeline_json,
        common_tasks=common_tasks,
        enable_caching=enable_caching,
        conditional_task_one=conditional_task_one,
        condtional_task_two=condtional_task_two,
        conditional_task_three=conditional_task_three,
    )
