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
    payload_path = f"pipelines/xgboost/training/payloads/{payload_file}"

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
        "extract-bq-to-dataset-4": ["dataset"],
        "generate-statistics": ["statistics"],
        "visualise-statistics": ["view"],
        "validate-schema": ["anomalies"],
        "show-anomalies": [],
        "train-xgboost-model": ["model", "metrics_artifact"],
        "lookup-model": ["model"],
        "predict-xgboost-model": ["predictions"],
        "calculate-eval-metrics": ["eval_metrics", "view"],
    }

    conditional_task_one = {
        "upload-model": [],
        "copy-artifact": ["des_artifact"],
    }

    condtional_task_two = {
        "export-model": ["model"],
        "predict-xgboost-model-2": ["predictions"],
        "calculate-eval-metrics-2": ["eval_metrics", "view"],
        "compare-models": [],
    }

    conditional_task_three = {
        "upload-model-2": [],
        "copy-artifact-2": ["des_artifact"],
    }

    pipeline_e2e_test(
        payload_path=payload_path,
        common_tasks=common_tasks,
        conditional_task_one=conditional_task_one,
        condtional_task_two=condtional_task_two,
        conditional_task_three=conditional_task_three,
    )
