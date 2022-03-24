from kfp.v2.dsl import Input, Output, Artifact, component
from pipelines.kfp_components.dependencies import PYTHON37, TENSORFLOW_DATA_VALIDATION


@component(base_image=PYTHON37, packages_to_install=[TENSORFLOW_DATA_VALIDATION])
def validate_skew(
    training_statistics_path: str,
    schema_path: str,
    anomalies: Output[Artifact],
    serving_statistics: Input[Artifact],
    environment: str = None,
) -> None:
    """
    Task which has the objective to wrap the tfdv.validate_statistics
    function, validating a statistics file according to a schema.
    For more details see:
    https://www.tensorflow.org/tfx/data_validation/api_docs/python/tfdv/validate_statistics

    Args:
        training_statistics_path (str): Path to training statistics file.
        schema_path (str): GCS uri path where the TFDV schema is stored.
        anomalies (Output[Artifact]): Output artifact consisting of a list of anomalies
                    serialised in protobuf text file.
        serving_statistics (Input[Artifact]): Input artifact to serving statistic file.
        environment (str): Optional {'TRAINING', 'SERVING', None}. Schema environment
                    to use during validation. Defaults to None.
    Returns:
        None
    """

    import logging
    import tensorflow_data_validation as tfdv

    def load_stats(path):
        logging.info(f"loading stats from: {path}")
        return tfdv.load_statistics(input_path=path)

    logging.getLogger().setLevel(logging.INFO)

    train_stats = load_stats(training_statistics_path)
    serving_stats = load_stats(serving_statistics.path)

    logging.info(f"loading schema from: {schema_path}")
    schema = tfdv.load_schema_text(schema_path)

    logging.info("validating stats...")
    # Validate statistics generated from serving data (`serving_stats`) against:
    # 1. the schema file (`schema`) in the specified environment (e.g. "SERVING")
    # 2. the statistics generated from training data (`train_stats`) for skew comparison
    detected_anomalies = tfdv.validate_statistics(
        statistics=serving_stats,
        schema=schema,
        environment=environment,
        serving_statistics=train_stats,
    )

    logging.info(f"writing anomalies to: {anomalies.path}")
    tfdv.write_anomalies_text(detected_anomalies, anomalies.path)
