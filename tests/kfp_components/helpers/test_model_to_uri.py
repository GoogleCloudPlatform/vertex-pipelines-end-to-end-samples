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

from kfp.v2.dsl import Model


def test_model_to_uri(tmpdir):
    """
    Test that model_to_uri returns: a uri that has len()>0, the correct model uri.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.helpers import model_to_uri

    model_path = tmpdir.join("/model")

    model = Model(uri=str(model_path))
    parent = False

    model_uri = model_to_uri(model, parent)

    assert len(model_uri) > 0
    assert model_uri == model.uri


def test_model_to_uri_parent(tmpdir):
    """
    Test that model_to_uri returns: a parent uri that has len()>0, the correct parent
    model uri.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.helpers import model_to_uri

    model_path = tmpdir.join("/parent_folder/model")
    model_path_parent = tmpdir.join("/parent_folder")

    model = Model(uri=str(model_path))
    parent = True

    model_uri_parent = model_to_uri(model, parent)

    assert len(model_uri_parent) > 0
    assert model_uri_parent == model_path_parent
