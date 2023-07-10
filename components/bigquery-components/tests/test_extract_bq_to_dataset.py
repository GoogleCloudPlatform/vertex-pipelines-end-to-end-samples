import google.cloud.bigquery  # noqa
from kfp.dsl import Dataset
from unittest import mock

import bigquery_components

extract_bq_to_dataset = bigquery_components.extract_bq_to_dataset.python_func


@mock.patch("google.cloud.bigquery.client.Client")
@mock.patch("google.cloud.bigquery.table.Table")
@mock.patch("google.cloud.bigquery.job.ExtractJobConfig")
def test_extract_bq_to_dataset(mock_job_config, mock_table, mock_client, tmpdir):
    """
    Checks that the extract_bq_to_dataset is called correctly
    """
    mock_path = tmpdir
    mock_client.extract_table.return_value = "my-job"
    mock_table.return_value.table_ref = "my-table"
    mock_job_config.return_value = "mock-job-config"

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

    mock_client.return_value.extract_table.assert_called_once_with(
        mock_table.return_value, "gs://mock_bucket", job_config="mock-job-config"
    )


@mock.patch("google.cloud.bigquery.client.Client")
@mock.patch("google.cloud.bigquery.table.Table")
@mock.patch("google.cloud.bigquery.job.ExtractJobConfig")
@mock.patch("pathlib.Path.exists")
def test_extract_bq_to_dataset_skip_existing(
    mock_path_exists, mock_job_config, mock_table, mock_client, tmpdir
):
    """
    Checks that when the dataset exists the method is not called
    """
    mock_path = tmpdir
    mock_path_exists.return_value = True

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

    assert not mock_client.return_value.extract_table.called
