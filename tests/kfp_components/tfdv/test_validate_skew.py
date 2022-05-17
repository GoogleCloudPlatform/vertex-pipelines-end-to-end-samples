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

from kfp.v2.dsl import Artifact
import tensorflow_data_validation as tfdv


def test_validate_skew(tmpdir, make_csv_file):
    """
    Assert that validate_skew produces an anomalies in protobuf text format file.

    Args:
        tmpdir: pytest tmpdir fixture
        make_csv_file: pytest fixture defined in conftest.py

    Returns:
        None
    """

    from pipelines.kfp_components.tfdv import validate_skew

    # prepare paths
    schema_path = "tests/kfp_components/tfdv/assets/validate_schema.pbtxt"
    data_path = str(tmpdir.join("train.csv"))
    train_stats_path = str(tmpdir.join("train.stats"))
    serve_stats_path = str(tmpdir.join("serve.stats"))
    anomalies_path = tmpdir.join("anomalies.pbtxt")

    # populate data
    make_csv_file(1, 100, data_path)

    train_stats = tfdv.generate_statistics_from_csv(data_path)
    tfdv.write_stats_text(train_stats, train_stats_path)

    serve_stats = tfdv.generate_statistics_from_csv(data_path)
    tfdv.write_stats_text(serve_stats, serve_stats_path)

    serve_statistics = Artifact(uri=serve_stats_path)
    anomalies = Artifact(uri=str(anomalies_path))

    validate_skew(
        training_statistics_path=train_stats_path,
        schema_path=schema_path,
        anomalies=anomalies,
        serving_statistics=serve_statistics,
        environment=None,
    )

    assert anomalies_path.exists()
