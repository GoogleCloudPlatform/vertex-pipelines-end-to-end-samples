# Copyright 2023 Google LLC
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

"""Load per-environment configuration from variables.yml."""

import os
import pathlib

import yaml


_ENVIRONMENTS = ("dev", "staging", "prod")
_VARIABLES_PATH = (
    pathlib.Path(__file__).parent.parent.parent.parent / "variables" / "variables.yml"
)


def detect_environment() -> str:
    """Infer the environment from the VERTEX_PROJECT_ID suffix.

    Matches a project id ending in ``-dev``, ``-staging`` or ``-prod``. When
    VERTEX_PROJECT_ID is unset (e.g. during compile / unit tests such as
    pr-checks) this defaults to ``dev``.

    Raises:
        ValueError: if VERTEX_PROJECT_ID is set but does not end with a known
            environment suffix.
    """
    project_id = os.environ.get("VERTEX_PROJECT_ID", "")
    if not project_id:
        return "dev"
    for suffix in ("prod", "staging", "dev"):
        if project_id.endswith(f"-{suffix}"):
            return suffix
    raise ValueError(
        f"Could not detect environment from VERTEX_PROJECT_ID='{project_id}'. "
        "Expected project ID to end with '-dev', '-staging', or '-prod'."
    )


def load_variables() -> dict:
    """Load variables.yml and return the config for the current environment.

    Global (top-level) keys are merged with the detected environment block;
    environment keys win on conflict.

    Raises:
        ValueError: if there is no configuration block for the detected
            environment.
    """
    with open(_VARIABLES_PATH) as f:
        config = yaml.safe_load(f)

    environment = detect_environment()
    env_config = config.get(environment)
    if env_config is None:
        raise ValueError(f"No configuration found for environment '{environment}'")

    global_keys = {k: v for k, v in config.items() if k not in _ENVIRONMENTS}
    return {**global_keys, **env_config}
