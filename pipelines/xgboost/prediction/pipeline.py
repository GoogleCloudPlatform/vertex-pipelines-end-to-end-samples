import json
import pathlib

from kfp.v2 import compiler, dsl
from google_cloud_pipeline_components.aiplatform import (
    ModelBatchPredictOp,
)

from pipelines import generate_query
from pipelines.kfp_components.aiplatform import lookup_model, get_current_time
from pipelines.kfp_components.bigquery import (
    extract_bq_to_dataset,
    bq_query_to_table,
)
from pipelines.kfp_components.tfdv import (
    validate_skew,
    generate_statistics,
    visualise_statistics,
    show_anomalies,
)


@dsl.pipeline(name="xgboost-prediction-pipeline")
def xgboost_pipeline(
    project_id: str,
    project_location: str,
    pipeline_files_gcs_path: str,
    ingestion_project_id: str,
    model_name: str,
    model_label: str,
    tfdv_schema_filename: str,
    tfdv_train_stats_path: str,
    dataset_id: str,
    dataset_location: str,
    ingestion_dataset_id: str,
    timestamp: str,
    batch_prediction_machine_type: str,
    batch_prediction_min_replicas: int,
    batch_prediction_max_replicas: int,
):
    """
    XGB prediction pipeline which:
     1. Extracts a dataset from BQ
     2. Validates training/serving skew
     3. Scores data to produce predictions in a BigQuery table

    Args:
        project_id (str): project id of the Google Cloud project
        project_location (str): location of the Google Cloud project
        pipeline_files_gcs_path (str): GCS path where the pipeline files are located
        ingestion_project_id (str): project id containing the source bigquery data
            for ingestion. This can be the same as `project_id` if the source data is
            in the same project where the ML pipeline is executed.
        model_name (str): name of model
        model_label (str): label of model
        tfdv_schema_filename (str): filename of schema generated by tfdv
            (in assets directory)
        tfdv_train_stats_path (str): path for statistics generated by tfdv
        dataset_id (str): id of BQ dataset used to store all staging data & predictions
        dataset_location (str): location of dataset
        ingestion_dataset_id (str): dataset id of ingestion data
        timestamp (str): Optional. Empty or a specific timestamp in ISO 8601 format
            (YYYY-MM-DDThh:mm:ss.sss±hh:mm or YYYY-MM-DDThh:mm:ss).
            If any time part is missing, it will be regarded as zero.
        batch_prediction_machine_type (str): Machine type to be used for Vertex Batch
            Prediction. Example machine_types - n1-standard-4, n1-standard-16 etc
        batch_prediction_min_replicas (int): Minimum no of machines to distribute the
            Vertex Batch Prediction job for horizontal scalability
        batch_prediction_max_replicas (int): Maximum no of machines to distribute the
            Vertex Batch Prediction job for horizontal scalability.

    Returns:
        None

    """

    # Create variables to ensure the same arguments are passed
    # into different components of the pipeline
    file_pattern = "files-*.csv"  # e.g. "files-*.csv", used as file pattern on storage
    time_column = "trip_start_timestamp"
    ingestion_table = "taxi_trips"
    table_suffix = "_xgb_prediction"  # suffix to table names
    ingested_table = "ingested_data" + table_suffix

    # generate sql queries which are used in ingestion and preprocessing
    # operations
    queries_folder = pathlib.Path(__file__).parent / "queries"

    time_filter = get_current_time(timestamp=timestamp).set_display_name(
        "Get time filter for ingestion query"
    )

    ingest_query = generate_query(
        queries_folder / "ingest.sql",
        source_dataset=f"{ingestion_project_id}.{ingestion_dataset_id}",
        source_table=ingestion_table,
        filter_column=time_column,
        filter_start_value=time_filter.output,
    )

    # data ingestion and preprocessing operations
    kwargs = dict(
        bq_client_project_id=project_id,
        destination_project_id=project_id,
        dataset_id=dataset_id,
        query_job_config=json.dumps(dict(write_disposition="WRITE_TRUNCATE")),
    )
    ingest = bq_query_to_table(
        query=ingest_query, table_id=ingested_table, **kwargs
    ).set_display_name("Ingest data")

    # data extraction to gcs
    data_for_validation = (
        extract_bq_to_dataset(
            bq_client_project_id=project_id,
            source_project_id=project_id,
            dataset_id=dataset_id,
            table_name=ingested_table,
            dataset_location=dataset_location,
            extract_job_config=json.dumps(
                dict(destination_format="CSV", field_delimiter=",", print_header="True")
            ),
            file_pattern=file_pattern,
        )
        .after(ingest)
        .set_display_name("Extract data to storage")
    )

    # Construct schema_path from base GCS path + filename
    tfdv_schema_path = (
        f"{pipeline_files_gcs_path}/prediction/assets/{tfdv_schema_filename}"
    )

    # validate training/serving skew
    serving_stats = generate_statistics(
        data_for_validation.outputs["dataset"],
        file_pattern=file_pattern,
        tfdv_stats_options=json.dumps(
            dict(
                schema=tfdv_schema_path,
                infer_type_from_schema=True,
            )
        ),
    ).set_display_name("Generate data statistics")
    # visualise statistics
    visualised_statistics = visualise_statistics(
        statistics=serving_stats.output,
        statistics_name="Serving Statistics",
        other_statistics_path=tfdv_train_stats_path,
        other_statistics_name="Training Statistics",
    ).set_display_name("Visualise data statistics")

    validated_skew = validate_skew(
        training_statistics_path=tfdv_train_stats_path,
        schema_path=tfdv_schema_path,
        serving_statistics=serving_stats.output,
        environment="SERVING",
    ).set_display_name("Validate data skew")

    anomalies = show_anomalies(
        anomalies=validated_skew.output, fail_on_anomalies=True
    ).set_display_name("Show anomalies")

    # lookup champion model
    champion_model = lookup_model(
        model_name=model_name,
        model_label=model_label,
        project_location=project_location,
        project_id=project_id,
        fail_on_model_not_found=True,
    ).set_display_name("Lookup champion model")

    # batch predict from BigQuery to BigQuery
    bigquery_source_input_uri = f"bq://{project_id}.{dataset_id}.{ingested_table}"
    bigquery_destination_output_uri = f"bq://{project_id}.{dataset_id}"

    batch_prediction = (
        ModelBatchPredictOp(
            project=project_id,
            job_display_name="my-xgboost-batch-prediction-job",
            location=project_location,
            model=champion_model.outputs["model"],
            instances_format="bigquery",
            predictions_format="bigquery",
            bigquery_source_input_uri=bigquery_source_input_uri,
            bigquery_destination_output_uri=bigquery_destination_output_uri,
            machine_type=batch_prediction_machine_type,
            starting_replica_count=batch_prediction_min_replicas,
            max_replica_count=batch_prediction_max_replicas,
        )
        .after(anomalies, ingest)
        .set_display_name("Vertex Batch Prediction for XGB model")
    )


def compile():
    """
    Uses the kfp compiler package to compile the pipeline function into a workflow yaml

    Args:
        None

    Returns:
        None
    """
    compiler.Compiler().compile(
        pipeline_func=xgboost_pipeline,
        package_path="prediction.json",
        type_check=False,
    )


if __name__ == "__main__":
    compile()
