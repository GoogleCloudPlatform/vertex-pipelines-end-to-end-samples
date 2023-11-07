# Copyright 2023 Google LLC
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

from kfp.dsl import Dataset, Output, component


@component(
    base_image="python:3.9",
    packages_to_install=["google-cloud-bigquery==2.30.0"],
)
def extract_table(
    bq_client_project_id: str,
    source_project_id: str,
    dataset_id: str,
    table_name: str,
    dataset: Output[Dataset],
    destination_gcs_uri: str = None,
    dataset_location: str = "EU",
    extract_job_config: dict = None,
    skip_if_exists: bool = True,
):
    """
    Extract BQ table in GCS.
    Args:
        bq_client_project_id (str): project id that will be used by the bq client
        source_project_id (str): project id from where BQ table will be extracted
        dataset_id (str): dataset id from where BQ table will be extracted
        table_name (str): table name (without project id and dataset id)
        dataset (Output[Dataset]): output dataset artifact generated by the operation,
            this parameter will be passed automatically by the orchestrator
        dataset_location (str): bq dataset location. Defaults to "EU".
        extract_job_config (dict): dict containing optional parameters
            required by the bq extract operation. Defaults to None.
            See available parameters here
            https://googleapis.dev/python/bigquery/latest/generated/google.cloud.bigquery.job.ExtractJobConfig.html # noqa
        destination_gcs_uri (str): GCS URI to use for saving query results (optional).

    Returns:
        Outputs (NamedTuple (str, list)): Output dataset directory and its  GCS uri.
    """

    import logging
    from pathlib import Path
    from google.cloud.exceptions import GoogleCloudError
    from google.cloud import bigquery

    # set uri of output dataset if destination_gcs_uri is provided
    if destination_gcs_uri:
        dataset.uri = destination_gcs_uri

    logging.info(f"Checking if destination exists: {dataset.path}")
    if Path(dataset.path).exists() and skip_if_exists:
        logging.info("Destination already exists, skipping table extraction!")
        return

    full_table_id = f"{source_project_id}.{dataset_id}.{table_name}"
    table = bigquery.table.Table(table_ref=full_table_id)

    if extract_job_config is None:
        extract_job_config = {}
    job_config = bigquery.job.ExtractJobConfig(**extract_job_config)

    logging.info(f"Extract table {table} to {dataset.uri}")
    client = bigquery.client.Client(
        project=bq_client_project_id, location=dataset_location
    )
    extract_job = client.extract_table(
        table,
        dataset.uri,
        job_config=job_config,
    )

    try:
        result = extract_job.result()
        logging.info("Table extracted, result: {}".format(result))
    except GoogleCloudError as e:
        logging.error(e)
        logging.error(extract_job.error_result)
        logging.error(extract_job.errors)
        raise e
