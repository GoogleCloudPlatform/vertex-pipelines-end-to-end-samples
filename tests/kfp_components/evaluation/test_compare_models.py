import pytest
from kfp.v2.dsl import Artifact


accuracy_1 = """{"Overall":{"accuracy": 0.9}}"""
accuracy_2 = """{"Overall":{"accuracy": 0.91}}"""
rmse_1 = """{"Overall":{"rmse": 0.1}}"""
rmse_2 = """{"Overall":{"rmse": 0.09}}"""


def test_compare_same_model(tmpdir):
    """
    Test compare_models where challenger/champion models have the same metrics but
    a 0.01 difference is needed for a model to supersede the other.
    """

    from pipelines.kfp_components.evaluation.compare_models import compare_models

    # Save metrics into a file & create Artifact object from it
    metrics_path = tmpdir.join("metrics.json")
    with open(metrics_path, "w") as file:
        file.write(accuracy_1)
    metrics = Artifact(uri=str(metrics_path))

    # comparing two models with the same metrics
    other_is_better = compare_models(
        metrics, metrics, "accuracy", higher_is_better=True, absolute_difference=0.01
    )  # accuracy should be at least 1% better

    # other model is not better
    assert not other_is_better


def test_compare_same_model_no_diff(tmpdir):
    """
    Test compare_models where challenger/champion models have the same metrics and no
    difference is needed for a model to supersede the other.
    """
    from pipelines.kfp_components.evaluation.compare_models import compare_models

    # Save metrics into a file & create Artifact object from it
    metrics_path = tmpdir.join("metrics.json")
    with open(metrics_path, "w") as file:
        file.write(accuracy_1)
    metrics = Artifact(uri=str(metrics_path))

    # comparing two models with the same metrics
    other_is_better = compare_models(
        metrics, metrics, "accuracy", higher_is_better=True, absolute_difference=0
    )  # no difference is considered better

    # metrics are the same, but still better given abs. diff. of 0
    assert other_is_better


def test_compare_accuracy(tmpdir):
    """
    Test compare_models where challenger models has metrics above threshold such that
    it supersedes the champion model.
    """
    from pipelines.kfp_components.evaluation.compare_models import compare_models

    # Save metrics into a file & create Artifact object from it
    metrics_path = tmpdir.join("metrics_1.json")
    with open(metrics_path, "w") as file:
        file.write(accuracy_1)
    metrics = Artifact(uri=str(metrics_path))

    other_metrics_path = tmpdir.join("metrics_2.json")
    with open(other_metrics_path, "w") as file:
        file.write(accuracy_2)
    other_metrics = Artifact(uri=str(other_metrics_path))

    other_is_better = compare_models(
        metrics,
        other_metrics,
        "accuracy",
        higher_is_better=True,
        absolute_difference=0.01,
    )  # accuracy should be at least 1% better

    # other model actually is 1% better
    assert other_is_better


def test_compare_accuracy_not_better(tmpdir):
    """
    Test compare_models where the challenger model has better metrics than the
    champion model, but the difference is not above threshold, so the challenger
    model does not supersede the champion.
    """

    from pipelines.kfp_components.evaluation.compare_models import compare_models

    # Save metrics into a file & create Artifact object from it
    metrics_path = tmpdir.join("metrics_1.json")
    with open(metrics_path, "w") as file:
        file.write(accuracy_1)
    metrics = Artifact(uri=str(metrics_path))

    other_metrics_path = tmpdir.join("metrics_2.json")
    with open(other_metrics_path, "w") as file:
        file.write(accuracy_2)
    other_metrics = Artifact(uri=str(other_metrics_path))

    other_is_better = compare_models(
        metrics,
        other_metrics,
        "accuracy",
        higher_is_better=True,
        absolute_difference=0.02,
    )  # accuracy should be at least 2% better

    # other model is not 2% better (just 1%)
    assert not other_is_better


def test_compare_rmse(tmpdir):
    """
    Test compare_models using RMSE as metric, where a lower value is indicative
    of better model performance.
    """
    from pipelines.kfp_components.evaluation.compare_models import compare_models

    # Save metrics into a file & create Artifact object from it
    metrics_path = tmpdir.join("metrics_1.json")
    with open(metrics_path, "w") as file:
        file.write(rmse_1)
    metrics = Artifact(uri=str(metrics_path))

    other_metrics_path = tmpdir.join("metrics_2.json")
    with open(other_metrics_path, "w") as file:
        file.write(rmse_2)
    other_metrics = Artifact(uri=str(other_metrics_path))

    other_is_better = compare_models(
        metrics, other_metrics, "rmse", higher_is_better=False, absolute_difference=1e-5
    )  # rmse should be slightly better

    # other model actually is better
    assert other_is_better


def test_compare_different_metrics_fail(tmpdir):
    """
    Test that compare_models raises a ValueError when one of the models lacks the
    comparison metric of choice.
    """
    from pipelines.kfp_components.evaluation.compare_models import compare_models

    # Save metrics into a file & create Artifact object from it
    metrics_path = tmpdir.join("metrics_1.json")
    with open(metrics_path, "w") as file:
        file.write(rmse_1)
    metrics = Artifact(uri=str(metrics_path))

    other_metrics_path = tmpdir.join("metrics_2.json")
    with open(other_metrics_path, "w") as file:
        file.write(accuracy_1)
    other_metrics = Artifact(uri=str(other_metrics_path))

    with pytest.raises(ValueError):
        compare_models(
            metrics,
            other_metrics,
            "rmse",
            higher_is_better=False,
            absolute_difference=1e-5,
        )
