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

from pipelines.tensorflow.training.pipeline import tensorflow_pipeline
from tests.e2e.test_e2e import pipeline_e2e_test


def test_pipeline_run(enable_caching) -> None:
    """
    Tests if pipeline is run successfully
    Triggers pipeline synchronously.
    Tests will fail if:
    - Any errors are thrown during execution
    - Any of the expected component outputs are empty (size == 0kb)

    Arguments:
        None

    Returns:
        None
    """
    pipeline_e2e_test(
        tensorflow_pipeline,
        common_tasks={},
        enable_caching=enable_caching,
    )
