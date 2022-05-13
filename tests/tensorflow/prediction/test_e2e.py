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

import os
from tests.e2e.test_e2e import pipeline_e2e_test


def test_pipeline_run() -> None:
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

    payload_file = os.environ["PAYLOAD"]
    payload_path = f"pipelines/tensorflow/prediction/payloads/{payload_file}"

    # tasks (components) and outputs for tasks which occur unconditionally
    common_tasks = {
        "get-current-time": [],
        "bq-query-to-table": [],
        "extract-bq-to-dataset": ["dataset"],
        "extract-bq-to-dataset-2": ["dataset"],
        "generate-statistics": ["statistics"],
        "validate-skew": ["anomalies"],
        "visualise-statistics": ["view"],
        "show-anomalies": [],
        "lookup-model": ["model"],
        "model-batch-predict": ["batchpredictionjob"],
        "load-dataset-to-bq": [],
    }

    pipeline_e2e_test(
        payload_path=payload_path,
        common_tasks=common_tasks,
    )
