import google.cloud.aiplatform as aip  # noqa
from kfp.v2.dsl import Dataset, Metrics, Artifact
from unittest import mock
import pytest
import json

import vertex_components

custom_train_job = vertex_components.custom_train_job.python_func


@mock.patch("google.cloud.aiplatform.CustomTrainingJob")
@mock.patch("os.path.exists")
@mock.patch("builtins.open", new_callable=mock.mock_open, read_data="{}")
def test_custom_train_job(mock_open, mock_exists, mock_job, tmpdir):
    """
    Checks that the custom job method is called
    """
    mock_exists.return_value = True

    mock_train_data = Dataset(uri=tmpdir)
    mock_valid_data = Dataset(uri=tmpdir)
    mock_test_data = Dataset(uri=tmpdir)
    mock_model = Artifact(uri=tmpdir, metadata={"resourceName": ""})
    mock_metrics = Metrics(uri=tmpdir)

    mock_job_instance = mock_job.return_value
    mock_job_instance.to_dict.return_value = {
        "trainingTaskMetadata": {"backingCustomJob": "mock_custom_job_name"}
    }

    (gcp_resources,) = custom_train_job(
        train_script_uri="gs://my-bucket/train_script.py",
        train_data=mock_train_data,
        valid_data=mock_valid_data,
        test_data=mock_test_data,
        project_id="my-project-id",
        project_location="europe-west4",
        model_display_name="my-model",
        train_container_uri="gcr.io/my-project/my-image:latest",
        serving_container_uri="gcr.io/my-project/my-serving-image:latest",
        model=mock_model,
        metrics=mock_metrics,
        staging_bucket="gs://my-bucket",
        job_name="my-job",
    )

    mock_job.assert_called_once_with(
        project="my-project-id",
        location="europe-west4",
        staging_bucket="gs://my-bucket",
        display_name="my-job",
        script_path="/gcs/my-bucket/train_script.py",
        container_uri="gcr.io/my-project/my-image:latest",
        requirements=None,
        model_serving_container_image_uri="gcr.io/my-project/my-serving-image:latest",  # noqa: E501
    )

    # Assert metrics loading
    mock_open.assert_called_once_with(tmpdir, "r")
    # Assert gcp_resources contains the expected value
    assert (
        json.loads(gcp_resources)["resources"][0]["resourceUri"]
        == "mock_custom_job_name"
    )


@mock.patch("google.cloud.aiplatform.CustomTrainingJob")
@mock.patch("os.path.exists")
@mock.patch("builtins.open", new_callable=mock.mock_open, read_data="{}")
def test_custom_train_script_not_found(mock_open, mock_exists, mock_job, tmpdir):
    """
    Checks that when the training script is not found
    the method fails
    """
    mock_exists.return_value = False

    mock_train_data = Dataset(uri=tmpdir)
    mock_valid_data = Dataset(uri=tmpdir)
    mock_test_data = Dataset(uri=tmpdir)
    mock_model = Artifact(uri=tmpdir, metadata={"resourceName": ""})
    mock_metrics = Metrics(uri=tmpdir)

    with pytest.raises(ValueError):
        (gcp_resources,) = custom_train_job(
            train_script_uri="gs://my-bucket/train_script.py",
            train_data=mock_train_data,
            valid_data=mock_valid_data,
            test_data=mock_test_data,
            project_id="my-project-id",
            project_location="europe-west4",
            model_display_name="my-model",
            train_container_uri="gcr.io/my-project/my-image:latest",
            serving_container_uri="gcr.io/my-project/my-serving-image:latest",
            model=mock_model,
            metrics=mock_metrics,
            staging_bucket="gs://my-bucket",
            job_name="my-job",
        )

    # Assert the custom training job is not executed
    mock_job.assert_not_called()
    mock_open.assert_not_called()
