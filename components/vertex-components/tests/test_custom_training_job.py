import google.cloud.aiplatform as aip  # noqa
from kfp.v2.dsl import Dataset, Metrics, Artifact
from unittest import mock
import pytest


import vertex_components

custom_train_job = vertex_components.custom_train_job.python_func


def test_custom_train_job(tmpdir):
    with mock.patch(
        "google.cloud.aiplatform.CustomTrainingJob"
    ) as mock_job, mock.patch("os.path.exists") as mock_exists, mock.patch(
        "builtins.open", mock.mock_open(read_data="{}")
    ) as mock_open:

        mock_exists.return_value = True

        mock_train_data = Dataset(uri=tmpdir)
        mock_valid_data = Dataset(uri=tmpdir)
        mock_test_data = Dataset(uri=tmpdir)

        mock_model = Artifact(uri=tmpdir, metadata={"resourceName": ""})
        mock_metrics = Metrics(uri=tmpdir)

        custom_train_job(
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

        mock_open.assert_called_once_with(tmpdir, "r")


def test_custom_train_script_not_found(tmpdir):
    with pytest.raises(ValueError), mock.patch(
        "google.cloud.aiplatform.CustomTrainingJob"
    ) as mock_job, mock.patch("os.path.exists") as mock_exists, mock.patch(
        "builtins.open", mock.mock_open(read_data="{}")
    ) as mock_open:

        mock_exists.return_value = False  # Simulate script path not found

        mock_train_data = Dataset(uri=tmpdir)
        mock_valid_data = Dataset(uri=tmpdir)
        mock_test_data = Dataset(uri=tmpdir)

        mock_model = Artifact(uri=tmpdir, metadata={"resourceName": ""})
        mock_metrics = Metrics(uri=tmpdir)

        custom_train_job(
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

        mock_job.assert_not_called()
        mock_open.assert_not_called()
