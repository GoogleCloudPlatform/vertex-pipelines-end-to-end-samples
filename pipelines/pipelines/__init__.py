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

from pathlib import Path
from jinja2 import Template


def generate_query(input_file: Path, **replacements) -> str:
    """
    Read input file and replace placeholder using Jinja.

    Args:
        input_file (Path): input file to read
        replacements: keyword arguments to use to replace placeholders
    Returns:
        str: replaced content of input file
    """

    with open(input_file, "r") as f:
        query_template = f.read()

    return Template(query_template).render(**replacements)
