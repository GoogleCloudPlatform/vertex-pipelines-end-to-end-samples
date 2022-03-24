import json
import pandas as pd
import numpy as np
from kfp.v2.dsl import Dataset, Artifact


def test_calculate_eval_metrics_overall(tmpdir):
    """
    Test that calculate_eval_metrics produces the specified metrics (mean squared
    error, accuracy, and mean label) at an overall level.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.evaluation import calculate_eval_metrics

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
    labels_data = Dataset(uri=labels_path)
    metrics_names = ["MeanSquaredError", "Accuracy", "MeanLabel"]
    label_column_name = "actual_label"
    pred_column_name = "predicted_label"
    evaluation_metrics = Artifact(uri=str(metrics_path))
    view_path = tmpdir.join("view.html")
    view = Artifact(uri=str(view_path))

    # Calculate evaluation metrics
    calculate_eval_metrics(
        labels_data,
        metrics_names,
        label_column_name,
        pred_column_name,
        evaluation_metrics,
        view,
    )

    # Read eval output into a dict
    with open(evaluation_metrics.path) as f:
        metrics_dict = json.load(f)

    # Check outputs
    assert "mean_squared_error" in metrics_dict["Overall"]
    assert "accuracy" in metrics_dict["Overall"]
    assert "mean_label" in metrics_dict["Overall"]


def test_calculate_eval_metrics_with_slice(tmpdir):
    """
    Test that calculate_eval_metrics produces the specified metrics (mean squared
    error, accuracy, and mean label) at an overall level + for slices.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.evaluation import calculate_eval_metrics

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
    labels_data = Dataset(uri=labels_path)
    metrics_names = ["MeanSquaredError", "Accuracy", "MeanLabel"]
    label_column_name = "actual_label"
    pred_column_name = "predicted_label"
    evaluation_metrics = Artifact(uri=str(metrics_path))
    view_path = tmpdir.join("view.html")
    view = Artifact(uri=str(view_path))
    slicing_specs = ['feature_keys: ["num_feat"]']

    # Calculate evaluation metrics
    calculate_eval_metrics(
        labels_data,
        metrics_names,
        label_column_name,
        pred_column_name,
        evaluation_metrics,
        view,
        slicing_specs=slicing_specs,
    )

    # Read eval output into a dict
    with open(evaluation_metrics.path) as f:
        metrics_dict = json.load(f)

    # Check outputs
    assert "mean_squared_error" in metrics_dict["Overall"]
    assert "accuracy" in metrics_dict["Overall"]
    assert "mean_label" in metrics_dict["Overall"]


def test_visualise_eval_metrics_overall(tmpdir):
    """
    Test that calculate_eval_metrics produces the specified output plot
        ("plots_overall.html) at an overall level

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.evaluation import calculate_eval_metrics

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
    labels_data = Dataset(uri=labels_path)
    metrics_names = ["MeanSquaredError", "Accuracy", "MeanLabel"]
    label_column_name = "actual_label"
    pred_column_name = "predicted_label"
    evaluation_metrics = Artifact(uri=str(metrics_path))
    view_path = tmpdir.join("plots_overall.html")
    view = Artifact(uri=str(view_path))

    # Calculate evaluation metrics
    calculate_eval_metrics(
        labels_data,
        metrics_names,
        label_column_name,
        pred_column_name,
        evaluation_metrics,
        view,
    )

    # Check outputs
    assert view_path.exists()
    assert view.path.endswith(".html")


def test_visualise_eval_metrics_with_slice(tmpdir):
    """
    Test that calculate_eval_metrics produces the specified output plot
        ("plots_overall.html) at an overall level and at a slice level
        (plots_num_feat.html)

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.evaluation import calculate_eval_metrics

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
    labels_data = Dataset(uri=labels_path)
    metrics_names = ["MeanSquaredError", "Accuracy", "MeanLabel"]
    label_column_name = "actual_label"
    pred_column_name = "predicted_label"
    evaluation_metrics = Artifact(uri=str(metrics_path))
    view_path = tmpdir.join("plots_overall.html")
    sliced_view_path = tmpdir.join("plots_num_feat.html")
    view = Artifact(uri=str(view_path))
    slicing_specs = ['feature_keys: ["num_feat"]']

    # Calculate evaluation metrics
    calculate_eval_metrics(
        labels_data,
        metrics_names,
        label_column_name,
        pred_column_name,
        evaluation_metrics,
        view,
        slicing_specs=slicing_specs,
    )

    # Check outputs
    assert view_path.exists()
    assert sliced_view_path.exists()
