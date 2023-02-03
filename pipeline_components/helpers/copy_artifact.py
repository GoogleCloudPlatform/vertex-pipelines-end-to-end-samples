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

from kfp.v2.dsl import Artifact, Input, Output, component
from pipelines.kfp_components.dependencies import PYTHON37


@component(base_image=PYTHON37)
def copy_artifact(
    src_artifact: Input[Artifact], des_artifact: Output[Artifact], des_uri: str = None
) -> None:
    """
    Copy artifact.

    Args:
        src_artifact (Input[Artifact]): Source artifact.
        des_artifact (Output[Artifact]): Copy of artifact
        des_uri (str): Optional. Set destination URI of copied artifact which includes
            the artifact itself. Defaults to None.

    Returns:
        None
    """
    import shutil
    from pathlib import Path

    if des_uri is not None:
        des_artifact.uri = des_uri

    # ensure parent folder(s) exist
    Path(des_artifact.path).parent.mkdir(parents=True, exist_ok=True)

    # copy artifact
    shutil.copy(src_artifact.path, des_artifact.path)
