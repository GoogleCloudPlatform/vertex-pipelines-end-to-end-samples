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
import pytest
from pathlib import Path


def test_successful_show_anomalies(tmpdir):
    """
    Assert that an anomalies in protobuf text format exists.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.tfdv import show_anomalies

    # Read in a correct anomalies string
    anomalies_path = Path("tests/kfp_components/tfdv/assets/correct_anomalies.pbtxt")
    anomalies = Artifact(uri=str(anomalies_path))
    fail_on_anomalies = True

    show_anomalies(anomalies=anomalies, fail_on_anomalies=fail_on_anomalies)

    assert anomalies_path.exists()


def test_failed_show_anomalies(tmpdir):
    """
    Ensure that an error is raised by show_anomalies when supplied with an anomalies
    protobuf text format file that has an incorrectly named field.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.tfdv import show_anomalies

    # Read in an incorrect anomalies string
    anomalies_path = Path("tests/kfp_components/tfdv/assets/incorrect_anomalies.pbtxt")
    anomalies = Artifact(uri=str(anomalies_path))
    fail_on_anomalies = True

    # Check that show_anomalies raises an Exception
    with pytest.raises(Exception):
        show_anomalies(anomalies=anomalies, fail_on_anomalies=fail_on_anomalies)
