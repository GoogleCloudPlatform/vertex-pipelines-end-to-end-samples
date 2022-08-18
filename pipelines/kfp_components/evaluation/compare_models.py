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

from kfp.v2.dsl import Input, Artifact, component
from pipelines.kfp_components.dependencies import PYTHON37


@component(base_image=PYTHON37)
def compare_models(
    metrics: Input[Artifact],
    other_metrics: Input[Artifact],
    evaluation_metric: str,
    higher_is_better: bool,
    absolute_difference: float = 0.0,
) -> bool:
    """Compare two models based on a single evaluation metric.

    Args:
        metrics (Input[Artifact]): metrics of 'champion model'
        other_metrics (Input[Artifact]): metrics of 'challenger model'
        evaluation_metric (str):
            name of metric for model comparison (e.g. rmse, accuracy etc.).
            the metric name must be present in the metadata of both metrics artifacts
        higher_is_better (bool): true if higher metric is better, otherwise false
        absolute_difference (float):
            a value >= 0 indicating the minimum absolute difference required
            for the 'challenger model' to outperform the 'champion model'.
            Defaults to 0.0.
    Returns:
        bool: True if 'challenger model' is better, otherwise False
    """
    import json
    import logging

    logging.getLogger().setLevel(logging.DEBUG)

    logging.info("Reading champion+challenger eval metric files into dict")
    with open(metrics.path) as f1:
        metrics_dict = json.load(f1)
    with open(other_metrics.path) as f2:
        other_metrics_dict = json.load(f2)

    if (evaluation_metric not in metrics_dict["Overall"]) or (
        evaluation_metric not in other_metrics_dict["Overall"]
    ):
        raise ValueError(f"'{evaluation_metric}' is not present in both metrics")

    if absolute_difference is None:
        logging.info("Since absolute_difference is None, setting it to 0.")
        absolute_difference = 0.0

    # get metrics from evaluation dict/s
    val = metrics_dict["Overall"][evaluation_metric]
    other_val = other_metrics_dict["Overall"][evaluation_metric]

    logging.info(f"comparing {evaluation_metric}: {val} vs. {other_val}")

    # ensure difference is absolute
    abs_diff = abs(absolute_difference)
    logging.info(f"minimum absolute difference: {abs_diff}")

    # calculate difference between metric values
    diff = other_val - val
    logging.info(f"actual difference: {diff}")

    # compare actual difference to minimum difference
    logging.info(
        f"For deciding on the better model, will {'NOT ' if not higher_is_better else ''}use higher is better"  # noqa: E501
    )
    other_is_better = (diff >= abs_diff) if higher_is_better else (diff <= abs_diff)
    logging.info(f"'other model' is better? {'Yes' if other_is_better else 'No'}.")

    return other_is_better
