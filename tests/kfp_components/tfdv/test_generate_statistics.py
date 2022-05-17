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

from kfp.v2.dsl import Dataset, Artifact
import tensorflow_data_validation as tfdv


def prep_stats_inputs(tmpdir, make_csv_file):
    """
    Prepare KFP artifacts that are needed for the generate_statistics function call.

    Args:
        tmpdir: built-in pytest tmpdir fixture
        make_csv_file: pytest fixture defined in conftest.py

    Returns:
        dataset: KFP Dataset object
        statistics: KFP artifact object
        stats_path (str): URI of the Artifact containing TFDV statistics
    """
    # Prepare paths
    data_path = str(tmpdir.join("train.csv"))
    stats_path = tmpdir.join("train.stats")

    # Create a dataset and put it in data_path
    make_csv_file(1, 100, data_path)

    # Prepare KFP objects
    dataset = Dataset(uri=data_path)
    statistics = Artifact(uri=str(stats_path))

    return dataset, statistics, stats_path


def test_generate_statistics_with_directrunner(tmpdir, make_csv_file):
    """
    Assert that statistics file is created by generate_statistics.

    Args:
        tmpdir: pytest tmpdir fixture
        make_csv_file: pytest fixture defined in conftest.py

    Returns:
        None
    """

    from pipelines.kfp_components.tfdv import generate_statistics

    dataset, statistics, stats_path = prep_stats_inputs(tmpdir, make_csv_file)
    beam_runner = "DirectRunner"

    generate_statistics(
        dataset=dataset,
        statistics=statistics,
    )

    # Check the statistics file is created
    assert stats_path.exists()

    # Check the statistics file is valid
    tfdv.load_statistics(input_path=statistics.path)
