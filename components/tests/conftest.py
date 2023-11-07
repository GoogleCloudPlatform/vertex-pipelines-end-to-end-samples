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

import pytest
import kfp.dsl


@pytest.fixture(autouse=True)
def mock_kfp_artifact(monkeypatch):
    """
    This fixture runs once after all tests are collected. It mocks the Artifact object
    (and thus any derived classes such as Dataset, Model, etc.) to return the URI as
    the path.

    Unit tests set the URI of artifacts, however, KFP components use Artifact.path to
    retrieve paths to files. If a URI doesn't start with gs:// or minio:// or s3://,
    the path with be None. This behaviour is avoided by mocking the Artifact._get_path
    method.

    Args:
        monkeypatch: Used to patch the decorator `@component` in `kfp.v2.dsl`.
            This prevents KFP from changing the Python functions when applying
            pytests.

    Returns:
        None

    """

    def _get_path(self):
        """
        Returns:
            str: The URI path of the Artifact
        """
        # simply return the URI
        return self.uri

    # mock the _get_path method of Artifact which is used by the property path
    monkeypatch.setattr(kfp.dsl.Artifact, "_get_path", _get_path)
