# Copyright 2022 Google LLC
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

from kfp.v2.dsl import Input, Output, Artifact, component
from pipelines.kfp_components.dependencies import PYTHON37, TENSORFLOW_DATA_VALIDATION


@component(base_image=PYTHON37, packages_to_install=[TENSORFLOW_DATA_VALIDATION])
def validate_schema(
    statistics: Input[Artifact],
    anomalies: Output[Artifact],
    schema_path: str,
) -> None:
    """
    Task which has the objective to wrap the tfdv.validate_statistics
    function, validating a statistics file according to a schema.

    Args:
        statistics (Input[Artifact]): Input artifact consisting of a statistics file.
            For more details see
            https://www.tensorflow.org/tfx/data_validation/api_docs/python/tfdv/validate_statistics
        anomalies (Output[Artifact]): Output artifact consisting of a list of anomalies
            serialised in JSON file.
        schema_path (str): GCS uri path where the tfdv schema is stored. For more details see
            https://www.tensorflow.org/tfx/data_validation/api_docs/python/tfdv/validate_statistics

    Returns:
        None
    """  # noqa

    import logging
    import tensorflow_data_validation as tfdv

    logging.getLogger().setLevel(logging.INFO)

    logging.info(f"loading stats from: {statistics.path}")
    dataset_statistics = tfdv.load_statistics(input_path=statistics.path)

    logging.info(f"loading schema from: {schema_path}")
    schema = tfdv.load_schema_text(schema_path)

    logging.info("validating stats...")
    detected_anomalies = tfdv.validate_statistics(
        statistics=dataset_statistics,
        schema=schema,
    )

    logging.info(f"writing anomalies to: {anomalies.path}")
    tfdv.write_anomalies_text(detected_anomalies, anomalies.path)
