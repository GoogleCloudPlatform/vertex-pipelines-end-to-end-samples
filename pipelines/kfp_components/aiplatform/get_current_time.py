# Copyright 2022 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from kfp.v2.dsl import component
from pipelines.kfp_components.dependencies import PYTHON37


@component(base_image=PYTHON37)
def get_current_time(timestamp: str) -> str:
    """
    Create time stamp for the filter in data ingestion step.
    If timestamp is empty, returns current time (UTC+0)
    in ISO 6801 date format. Otherwise, returns input timestamp.
    If the input timestamp is specified, it must follow ISO 6801 date format,
    which consist of two parts, date and time. For example 2022-01-18T19:00:00.
    The date part is mandatory while any missing value in time part
    will be regarded as zero.

    Args:
        timestamp (str): Optional. Empty or
        a specific timestamp in ISO 8601 format

    Returns:
        str: A string of current times in ISO 8601 format or
        a specific timestamp in ISO 8601 format.
    """
    from datetime import datetime, timezone
    import logging

    if not timestamp:
        return datetime.now(timezone.utc).isoformat()

    else:
        try:
            logging.info(
                f"timestamp in ISO 8601 format: \
                {datetime.fromisoformat(timestamp)}"
            )
            return datetime.fromisoformat(timestamp).isoformat()
        except ValueError:
            raise ValueError(
                f"timestamp is not in correct ISO 6801 format \
                    (YYYY-MM-DD or YYYY-MM-DD hh:mm:ss or \
                    YYYY-MM-DDThh:mm:ss.sss±hh:mm)\
                    or an empty string"
            )
