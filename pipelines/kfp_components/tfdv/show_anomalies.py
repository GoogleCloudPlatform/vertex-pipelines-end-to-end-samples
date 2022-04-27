from kfp.v2.dsl import Input, Artifact, component
from pipelines.kfp_components.dependencies import PYTHON37, TENSORFLOW_DATA_VALIDATION


@component(base_image=PYTHON37, packages_to_install=[TENSORFLOW_DATA_VALIDATION])
def show_anomalies(
    anomalies: Input[Artifact],
    fail_on_anomalies: bool = True,
    anomaly_code_ignore_list: list = None,
) -> None:
    """
    Analyzes an anomaly protobuf and reports the status.

    Args:
        anomalies (Input[Artifact]): Input anomalies in protobuf text format.
        fail_on_anomalies (bool): Whether this step should fail if any anomalies are
            found. Defaults to True.
        anomaly_code_ignore_list: Optional list of codes of anomaly types to ignore as
            anomalies. This list needs to contain the codes as integers &
            NOT the anomaly types as strings.
            Some examples of anomaly types include:
            1. Code 19: FEATURE_TYPE_NOT_PRESENT - Column either not present
               or has 100% nulls
            2. Code 16: FEATURE_TYPE_LOW_FRACTION_PRESENT - % of non-null values in
               a column is lower than expected
            Reference for comprehensive list of anomaly types & their codes:
            https://www.tensorflow.org/tfx/data_validation/anomalies
            https://github.com/tensorflow/metadata/blob/master/tensorflow_metadata/proto/v0/anomalies.proto


    Returns:
        None
    """

    import logging
    import tensorflow_data_validation as tfdv
    from tensorflow_data_validation.utils.anomalies_util import remove_anomaly_types

    logging.getLogger().setLevel(logging.INFO)

    # Load all anomalies
    logging.info(f"For details of all anomalies, please refer to {anomalies.uri}")
    detected_anomalies = tfdv.load_anomalies_text(anomalies.path)

    # Loop through all anomalies and log details
    for key, val in detected_anomalies.anomaly_info.items():
        logging.warning(f"found anomaly for key {key}, reason: {val.short_description}")

    # If defined, remove all anomalies in the ignore list
    if anomaly_code_ignore_list:
        logging.info(f"Ignoring all anomalies of code: {anomaly_code_ignore_list}")
        #  remove_anomaly_types does an in-place removal of all anomalies
        #  in the ignore list
        remove_anomaly_types(
            anomalies=detected_anomalies,
            types_to_remove=anomaly_code_ignore_list,
        )

    # If there are anomalies, decide whether to fail
    if detected_anomalies.anomaly_info and fail_on_anomalies:
        msg = f"Found {len(detected_anomalies.anomaly_info)} anomalies, failing!"
        logging.error(msg)
        raise RuntimeError(msg)
