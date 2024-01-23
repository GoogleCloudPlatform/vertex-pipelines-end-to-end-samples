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
from kfp.dsl import Dataset, Output, ContainerSpec, container_component


@container_component
def extract_table(
    project: str,
    location: str,
    table: str,
    data: Output[Dataset],
    destination_format: str = "CSV",
    compression: str = "NONE",
    field_delimiter: str = ",",
    print_header: str = "true",
):
    return ContainerSpec(
        image="google/cloud-sdk:alpine",
        command=["bq"],
        args=[
            "extract",
            f"--project_id={project}",
            f"--location={location}",
            f"--destination_format={destination_format}",
            f"--compression={compression}",
            f"--field_delimiter={field_delimiter}",
            f"--print_header={print_header}",
            table,
            data.uri,
        ],
    )
