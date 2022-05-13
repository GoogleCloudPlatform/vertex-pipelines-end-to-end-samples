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

from kfp.v2.dsl import Input, Model, component
from pipelines.kfp_components.dependencies import PYTHON37


@component(base_image=PYTHON37)
def model_to_uri(model: Input[Model], parent: bool = True) -> str:
    """
    Return the URI of a model.

    Args:
        model (Input[Model]): Input model.
        parent (bool): Whether to return the URI of the parent folder. Defaults to True.

    Returns:
        str: URI of model (or URI of its parent folder).
    """

    uri = model.uri
    if parent:
        uri = uri.rsplit("/", 1)[0]
    return uri
