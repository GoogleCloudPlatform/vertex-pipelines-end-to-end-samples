import json
import pathlib

from kfp.v2 import compiler, dsl
from google_cloud_pipeline_components.experimental.custom_job.utils import (
    create_custom_training_job_op_from_component,
)
from pipelines import generate_query
from pipelines.kfp_components.dependencies import SKL_SERVING_CONTAINER_IMAGE_URI
from pipelines.kfp_components.aiplatform import (
    upload_model,
)
from pipelines.kfp_components.bigquery import extract_bq_to_dataset, bq_query_to_table

from pipelines.kfp_components.xgboost import train_xgboost_model


@dsl.pipeline(name="xgboost-train-pipeline")
def xgboost_pipeline(
    pipeline_files_gcs_path: str,
    project_id: str,
    project_location: str,
    ingestion_project_id: str,
    model_name: str,
    model_label: str,
    dataset_id: str,
    dataset_location: str,
    ingestion_dataset_id: str,
    timestamp: str,
):
    """
    XGB training pipeline which:
     1. Extracts a dataset from BQ
     2. Splits the dataset into train+validate sets (80:20)
     3. Trains the model via Vertex AI CustomTrainJob
     4. Pushes the model to Vertex AI Model Registry

    Args:
        project_id (str): project id of the Google Cloud project
        project_location (str): location of the Google Cloud project
        pipeline_files_gcs_path (str): GCS path where the pipeline files are located
        ingestion_project_id (str): project id containing the source bigquery data
            for ingestion. This can be the same as `project_id` if the source data is
            in the same project where the ML pipeline is executed.
        model_name (str): name of model
        model_label (str): label of model
        dataset_id (str): id of BQ dataset used to store all staging data & predictions
        dataset_location (str): location of dataset
        ingestion_dataset_id (str): dataset id of ingestion data
        timestamp (str): Optional. Empty or a specific timestamp in ISO 8601 format
            (YYYY-MM-DDThh:mm:ss.sss±hh:mm or YYYY-MM-DDThh:mm:ss).
            If any time part is missing, it will be regarded as zero.


    Returns:
        None

    """

    # Create variables to ensure the same arguments are passed
    # into different components of the pipeline
    file_pattern = ""  # e.g. "files-*.csv", used as file pattern on storage
    label_column_name = "total_fare"
    pred_column_name = "predictions"
    time_column = "trip_start_timestamp"
    metrics_names = ["MeanSquaredError"]
    ingestion_table = "taxi_trips"
    table_suffix = "_xgb_training"  # suffix to table names
    ingested_table = "ingested_data" + table_suffix
    preprocessed_table = "preprocessed_data" + table_suffix
    train_table = "train_data" + table_suffix
    valid_table = "valid_data" + table_suffix
    test_table = "test_data" + table_suffix

    # generate sql queries which are used in ingestion and preprocessing
    # operations

    queries_folder = pathlib.Path(__file__).parent / "queries"

    ingest_query = generate_query(
        queries_folder / "ingest.sql",
        source_dataset=f"{ingestion_project_id}.{ingestion_dataset_id}",
        source_table=ingestion_table,
        filter_column=time_column,
        target_column=label_column_name,
        filter_start_value=timestamp,
    )
    split_train_query = generate_query(
        queries_folder / "sample.sql",
        source_dataset=dataset_id,
        source_table=ingested_table,
        num_lots=10,
        lots=tuple(range(8)),
    )
    split_valid_query = generate_query(
        queries_folder / "sample.sql",
        source_dataset=dataset_id,
        source_table=ingested_table,
        num_lots=10,
        lots=tuple(range(9,11)),
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

    split_train_data = (
        bq_query_to_table(query=split_train_query, table_id=train_table, **kwargs)
        .after(ingest)
        .set_display_name("Split train data")
    )
    split_valid_data = (
        bq_query_to_table(query=split_valid_query, table_id=valid_table, **kwargs)
        .after(ingest)
        .set_display_name("Split validation data")
    )

    # data extraction to gcs

    train_dataset = (
        extract_bq_to_dataset(
            bq_client_project_id=project_id,
            source_project_id=project_id,
            dataset_id=dataset_id,
            table_name=preprocessed_table,
            dataset_location=dataset_location,
            file_pattern=file_pattern,
        )
        .after(split_train_data)
        .set_display_name("Extract train data to storage")
    )
    valid_dataset = (
        extract_bq_to_dataset(
            bq_client_project_id=project_id,
            source_project_id=project_id,
            dataset_id=dataset_id,
            table_name=valid_table,
            dataset_location=dataset_location,
            file_pattern=file_pattern,
        )
        .after(split_valid_data)
        .set_display_name("Extract validation data to storage")
    )

    # train xgboost model
    """
    scikit-learn version for training job requirement, local predict component,
    train image & serving image need to be in sync
    Training job req - v0.24.1
    Local predict - v0.24.1
    Training image - v0.23.1 (latest available)
    Serving image - v0.24.1 (latest available)
    """
    model_params = dict(
        n_estimators=200,
        early_stopping_rounds=10,
        objective="reg:squarederror",
        booster="gbtree",
        learning_rate=0.3,
        min_split_loss=0,
        max_depth=6,
    )

    train_model = (
        custom_train_job(
            training_data=train_dataset.outputs["dataset"],
            validation_data=valid_dataset.outputs["dataset"],
            file_pattern=file_pattern,
            label_name=label_column_name,
            model_params=json.dumps(model_params),
            # Training wrapper specific parameters
            project=project_id,
            location=project_location,
        )
        .after(train_dataset)
        .set_display_name("Vertex Training for XGB model")
    )

    model = train_model.outputs["model"]
    metrics_artifact = train_model.outputs["metrics_artifact"]

    # Upload model
    upload_model(
        display_name=model_name,
        serving_container_image_uri=SKL_SERVING_CONTAINER_IMAGE_URI,
        model=model,
        project_id=project_id,
        project_location=project_location,
        description="",
        labels=json.dumps(
            dict(
                model_label=f"{model_label}",
                pipeline_job_uuid="{{$.pipeline_job_uuid}}",
                pipeline_job_name="{{$.pipeline_job_name}}",
            )
        ),
    ).set_display_name("Upload trained model")

 


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
        package_path="training.json",
        type_check=False,
    )


if __name__ == "__main__":
    custom_train_job = create_custom_training_job_op_from_component(
        component_spec=train_xgboost_model,
        replica_count=1,
        machine_type="n1-standard-4",
    )
    compile()
