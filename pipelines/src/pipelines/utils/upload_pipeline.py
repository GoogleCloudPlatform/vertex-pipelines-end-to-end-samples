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
import argparse
from typing import List
from kfp.registry import RegistryClient


def upload_pipeline(host: str, file_name: str, tags: List[str]) -> tuple[str, str]:
    """Upload a compiled YAML pipeline to Artifact Registry

    Args:
        host (str): URL of the Artifact Registry repository
        file_name (str): File path to the compiled YAML pipeline
        tags (List[str]): List of tags to use for the uploaded pipeline

    Returns:
        A tuple of the package name and the version.
    """

    client = RegistryClient(
        host=host,
    )

    return client.upload_pipeline(
        file_name=file_name,
        tags=tags,
    )


def main(args: List[str] = None):
    """CLI entrypoint for the upload_pipeline.py script"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", type=str, required=True)
    parser.add_argument("--yaml", type=str, required=True)
    parser.add_argument("--tag", type=str, action="append")
    parsed_args = parser.parse_args(args)

    upload_pipeline(
        host=parsed_args.dest,
        file_name=parsed_args.yaml,
        tags=parsed_args.tag,
    )


if __name__ == "__main__":
    main()
