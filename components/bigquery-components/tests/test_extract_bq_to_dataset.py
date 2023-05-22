import google.cloud.bigquery  # noqa
from kfp.v2.dsl import Dataset
from unittest import mock

import bigquery_components

extract_bq_to_dataset = bigquery_components.extract_bq_to_dataset.python_func


def test_extract_bq_to_dataset(tmpdir):
    with mock.patch("google.cloud.bigquery.client.Client") as mock_client, mock.patch(
        "google.cloud.bigquery.job.ExtractJobConfig"
    ) as mock_job_config, mock.patch("google.cloud.bigquery.table.Table") as mock_table:

        # Mock the Dataset path
        mock_path = tmpdir

        # Set up the mock Client
        mock_client.extract_table.return_value = "my-job"

        # Set up the mock Table
        mock_table.return_value.table_ref = "my-table"

        # Set up the mock ExtractJob
        mock_job_config.return_value = "mock-job-config"

        # Call the function
        extract_bq_to_dataset(
            bq_client_project_id="my-project-id",
            source_project_id="source-project-id",
            dataset_id="dataset-id",
            table_name="table-name",
            dataset=Dataset(uri=mock_path),
            destination_gcs_uri="gs://mock_bucket",
            dataset_location="EU",
            extract_job_config=None,
            skip_if_exists=False,
        )

        # Check that client.extract_table was called correctly
        mock_client.return_value.extract_table.assert_called_once_with(
            mock_table.return_value, "gs://mock_bucket", job_config="mock-job-config"
        )


def test_extract_bq_to_dataset_skip_existing(tmpdir):
    with mock.patch("google.cloud.bigquery.client.Client") as mock_client, mock.patch(
        "google.cloud.bigquery.table.Table"
    ), mock.patch("google.cloud.bigquery.job.ExtractJobConfig"), mock.patch(
        "pathlib.Path.exists"
    ) as mock_path_exists:

        # Mock the Dataset path
        mock_path = tmpdir

        # Mock that the destination already exists
        mock_path_exists.return_value = True

        # Call the function
        extract_bq_to_dataset(
            bq_client_project_id="my-project-id",
            source_project_id="source-project-id",
            dataset_id="dataset-id",
            table_name="table-name",
            dataset=Dataset(uri=mock_path),
            destination_gcs_uri="gs://mock_bucket",
            dataset_location="EU",
            extract_job_config=None,
            skip_if_exists=True,
        )

        # Ensure that Client.extract_table was not called
        assert not mock_client.return_value.extract_table.called
