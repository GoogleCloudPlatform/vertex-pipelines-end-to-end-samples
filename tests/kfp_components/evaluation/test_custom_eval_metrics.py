import json
import pandas as pd
import numpy as np
from kfp.v2.dsl import Dataset, Artifact
import shutil

from unittest import mock

# This is the name of the module (without the .py extension) that contains the class
MODULE_TO_TEST = "example_count"

# This is the name of the class that defines the metric
CLASS_TO_TEST = "ExampleCount_Custom"

# This is the name given to the class inside the module
CLASS_NAME_TO_TEST = "example_count_custom"


def mock_download(tmpdir, local_path):
    tmp_path = f"{tmpdir}/{MODULE_TO_TEST}.py"
    shutil.copy(local_path, tmp_path)


def test_calculate_custom_eval_metrics_overall(tmpdir):
    """
    Test that calculate_eval_metrics produces the specified metrics (mean squared
    error, accuracy, and mean label) at an overall level.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.evaluation import calculate_eval_metrics
    from pipelines.tensorflow.training.assets.tfma_custom_metrics import example_count

    metric_to_evaluate = example_count.ExampleCount_Custom

    # Create a uri for the Metrics artifact which the kfp_component writes to
    # Without this the artifact has no path and can't be written to
    metrics_path = tmpdir.join("eval_metrics")  #  Without .json

    # Generate random labels (actual and predicted)
    n_cols, n_rows = 2, 1000
    columns = ["actual_label", "predicted_label"]
    labels_path = str(tmpdir.join("labels.csv"))
    pd.DataFrame(np.random.rand(n_rows, n_cols), columns=columns).to_csv(
        labels_path, index=False
    )

    # Prepare arguments
    """
    This is the metric you want to test
    Need to ensure that this custom metric exists in the module
    """
    custom_metrics = {CLASS_TO_TEST: MODULE_TO_TEST}
    local_path = f"""
./pipelines/tensorflow/training/
assets/tfma_custom_metrics/{MODULE_TO_TEST}.py
""".replace(
        "\n", ""
    )
    labels_data = Dataset(uri=labels_path)
    metrics_names = []
    label_column_name = "actual_label"
    pred_column_name = "predicted_label"
    evaluation_metrics = Artifact(uri=str(metrics_path))
    view_path = tmpdir.join("view.html")
    view = Artifact(uri=str(view_path))

    with mock.patch("google.cloud.storage.Client") as mock_client, mock.patch(
        "google.cloud.storage.blob.Blob"
    ) as mock_blob:
        mock_blob.download_blob_to_file.side_effect = mock_download(tmpdir, local_path)
        # Calculate evaluation metrics
        calculate_eval_metrics(
            labels_data,
            metrics_names,
            label_column_name,
            pred_column_name,
            evaluation_metrics,
            view,
            custom_metrics=custom_metrics,
            custom_metrics_path=mock_blob.download_blob_to_file.side_effect,
        )

    # Read eval output into a dict
    with open(evaluation_metrics.path) as f:
        metrics_dict = json.load(f)

    # Check outputs
    assert CLASS_NAME_TO_TEST in metrics_dict["Overall"]


def test_calculate_custom_eval_metrics_with_slice(tmpdir):
    """
    Test that calculate_eval_metrics produces the specified metrics (mean squared
    error, accuracy, and mean label) at an overall level + for slices.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.evaluation import calculate_eval_metrics
    from pipelines.tensorflow.training.assets.tfma_custom_metrics import example_count

    metric_to_evaluate = example_count.ExampleCount_Custom

    # Create a uri for the Metrics artifact which the kfp_component writes to
    # Without this the artifact has no path and can't be written to
    metrics_path = tmpdir.join("eval_metrics")  #  Without .json

    # Generate random labels (actual and predicted)
    n_cols, n_rows = 3, 1000
    columns = ["num_feat", "actual_label", "predicted_label"]
    labels_path = str(tmpdir.join("labels.csv"))
    pd.DataFrame(np.random.rand(n_rows, n_cols), columns=columns).to_csv(
        labels_path, index=False
    )

    # Prepare arguments
    """
    This is the metric you want to test
    Need to ensure that this custom metric exists in the module
    """
    custom_metrics = {CLASS_TO_TEST: MODULE_TO_TEST}
    local_path = f"""
./pipelines/tensorflow/training/
assets/tfma_custom_metrics/{MODULE_TO_TEST}.py
""".replace(
        "\n", ""
    )
    labels_data = Dataset(uri=labels_path)
    metrics_names = ["MeanSquaredError", "Accuracy", "MeanLabel"]
    label_column_name = "actual_label"
    pred_column_name = "predicted_label"
    evaluation_metrics = Artifact(uri=str(metrics_path))
    view_path = tmpdir.join("view.html")
    view = Artifact(uri=str(view_path))
    slicing_specs = ['feature_keys: ["num_feat"]']

    with mock.patch("google.cloud.storage.Client") as mock_client, mock.patch(
        "google.cloud.storage.blob.Blob"
    ) as mock_blob:
        mock_blob.download_blob_to_file.side_effect = mock_download(tmpdir, local_path)
        # Calculate evaluation metrics
        calculate_eval_metrics(
            labels_data,
            metrics_names,
            label_column_name,
            pred_column_name,
            evaluation_metrics,
            view,
            slicing_specs=slicing_specs,
            custom_metrics=custom_metrics,
            custom_metrics_path=mock_blob.download_blob_to_file.side_effect,
        )

    # Read eval output into a dict
    with open(evaluation_metrics.path) as f:
        metrics_dict = json.load(f)

    # Check outputs
    assert CLASS_NAME_TO_TEST in metrics_dict["Overall"]
