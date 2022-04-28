# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Squared pearson correlation (r^2) metric."""

from typing import Dict, Iterable, Optional

import apache_beam as beam
from tensorflow_model_analysis.metrics import metric_types
from tensorflow_model_analysis.metrics import metric_util
from tensorflow_model_analysis.proto import config_pb2

SQUARED_PEARSON_CORRELATION_NAME = "squared_pearson_correlation"


class SquaredPearson(metric_types.Metric):
    """Squared pearson correlation (r^2) metric."""

    def __init__(self, name: str = SQUARED_PEARSON_CORRELATION_NAME):
        """Initializes squared pearson correlation (r^2) metric.
        Args:
          name (str): Metric name.
        """
        super().__init__(
            metric_util.merge_per_key_computations(_squared_pearson_correlation),
            name=name,
        )


metric_types.register_metric(SquaredPearson)


def _squared_pearson_correlation(
    name: str = SQUARED_PEARSON_CORRELATION_NAME,
    eval_config: Optional[config_pb2.EvalConfig] = None,
    model_name: str = "",
    output_name: str = "",
    sub_key: Optional[metric_types.SubKey] = None,
    aggregation_type: Optional[metric_types.AggregationType] = None,
    class_weights: Optional[Dict[int, float]] = None,
    example_weighted: bool = False,
) -> metric_types.MetricComputations:
    """Returns metric computations for squared pearson correlation (r^2).
    Args:
        name (str): Metric name
        eval_config (EvalConfig): Configuration of evaluation job used by Beam
        model_names (list): List of model names to evaluate
        output_names (list): List of model output names to evaluate
        sub_keys (list): Sub keys to use (class ID, top K or K)
        aggregation_type (AggregationType): If any aggregation is used, specify which
            type
        class_weights (dict): Different weights applied to classes during classification
        example_weighted (bool): Specify if extra weight needs to be applied to
            any example

    Returns:
        computations: List of steps that will be computed by Beam"""
    key = metric_types.MetricKey(
        name=name,
        model_name=model_name,
        output_name=output_name,
        sub_key=sub_key,
        example_weighted=example_weighted,
    )
    return [
        metric_types.MetricComputation(
            keys=[key],
            preprocessor=None,
            combiner=_SquaredPearsonCorrelationCombiner_Custom(
                key, eval_config, aggregation_type, class_weights, example_weighted
            ),
        )
    ]


class _SquaredPearsonCorrelationAccumulator_Custom:
    """Initialise the squared pearson correlation (r^2) accumulator. This will set
    all intermediate metrics computed by the accumulator to 0
    """

    __slots__ = [
        "total_weighted_labels",
        "total_weighted_predictions",
        "total_weighted_squared_labels",
        "total_weighted_squared_predictions",
        "total_weighted_labels_times_predictions",
        "total_weighted_examples",
    ]

    def __init__(self):
        self.total_weighted_labels = 0.0
        self.total_weighted_predictions = 0.0
        self.total_weighted_squared_labels = 0.0
        self.total_weighted_squared_predictions = 0.0
        self.total_weighted_labels_times_predictions = 0.0
        self.total_weighted_examples = 0.0


class _SquaredPearsonCorrelationCombiner_Custom(beam.CombineFn):
    """Computes squared pearson correlation (r^2) metric.
    Args:
        key (MetricKey): Metric key used in the evaluation
        eval_config (EvalConfig): Configuration of evaluation job used by Beam
        aggregation_type (AggregationType): If any aggregation is used, specify which
            type
        class_weights (dict): Different weights applied to classes during classification
        example_weighted (bool): Specify if extra weight needs to be applied to
            any example"""

    def __init__(
        self,
        key: metric_types.MetricKey,
        eval_config: Optional[config_pb2.EvalConfig],
        aggregation_type: Optional[metric_types.AggregationType],
        class_weights: Optional[Dict[int, float]],
        example_weighted: bool,
    ):
        self._key = key
        self._eval_config = eval_config
        self._aggregation_type = aggregation_type
        self._class_weights = class_weights
        self._example_weighted = example_weighted

    def create_accumulator(self) -> _SquaredPearsonCorrelationAccumulator_Custom:
        return _SquaredPearsonCorrelationAccumulator_Custom()

    def add_input(
        self,
        accumulator: _SquaredPearsonCorrelationAccumulator_Custom,
        element: metric_types.StandardMetricInputs,
    ) -> _SquaredPearsonCorrelationAccumulator_Custom:
        """Computes intermediate calculations required for the squared Pearson corr.
        Args:
            accumulator (Accumulator): Accumulator where the results will be added to
            element (StandardMetricInput): Item that contains the label that
                 needs evaluation
        """
        for (
            label,
            prediction,
            example_weight,
        ) in metric_util.to_label_prediction_example_weight(
            element,
            eval_config=self._eval_config,
            model_name=self._key.model_name,
            output_name=self._key.output_name,
            aggregation_type=self._aggregation_type,
            class_weights=self._class_weights,
            example_weighted=self._example_weighted,
        ):
            example_weight = float(example_weight)
            label = float(label)
            prediction = float(prediction)
            accumulator.total_weighted_labels += example_weight * label
            accumulator.total_weighted_predictions += example_weight * prediction
            accumulator.total_weighted_squared_labels += example_weight * label**2
            accumulator.total_weighted_squared_predictions += (
                example_weight * prediction**2
            )
            accumulator.total_weighted_labels_times_predictions += (
                example_weight * label * prediction
            )
            accumulator.total_weighted_examples += example_weight
        return accumulator

    def merge_accumulators(
        self, accumulators: Iterable[_SquaredPearsonCorrelationAccumulator_Custom]
    ) -> _SquaredPearsonCorrelationAccumulator_Custom:
        """Merges all accumulators that have been processed in parallel together
        Args:
            accumulators (Accumulator): Accumulator containing the results of
                every processed chunk

        Returns:
            result: Combined intermediate metrics for all accumulators
        """
        accumulators = iter(accumulators)
        result = next(accumulators)
        for accumulator in accumulators:
            result.total_weighted_labels += accumulator.total_weighted_labels
            result.total_weighted_predictions += accumulator.total_weighted_predictions
            result.total_weighted_squared_labels += (
                accumulator.total_weighted_squared_labels
            )
            result.total_weighted_squared_predictions += (
                accumulator.total_weighted_squared_predictions
            )
            result.total_weighted_labels_times_predictions += (
                accumulator.total_weighted_labels_times_predictions
            )
            result.total_weighted_examples += accumulator.total_weighted_examples
        return result

    def extract_output(
        self, accumulator: _SquaredPearsonCorrelationAccumulator_Custom
    ) -> Dict[metric_types.MetricKey, float]:
        """Extracts output from the merged accumulator and returns the final results
        Args:
            accumulator (float): Merged accumulator

        Returns:
            dict: Final results for every key"""
        result = float("nan")

        if accumulator.total_weighted_examples > 0.0:
            # See https://en.wikipedia.org/wiki/Pearson_correlation_coefficient
            numerator = (
                accumulator.total_weighted_labels_times_predictions
                - accumulator.total_weighted_labels
                * accumulator.total_weighted_predictions
                / accumulator.total_weighted_examples
            ) ** 2

            denominator_y = (
                accumulator.total_weighted_squared_predictions
                - accumulator.total_weighted_predictions**2
                / accumulator.total_weighted_examples
            )

            denominator_x = (
                accumulator.total_weighted_squared_labels
                - accumulator.total_weighted_labels**2
                / accumulator.total_weighted_examples
            )
            denominator = denominator_x * denominator_y
            if denominator > 0.0:
                result = numerator / denominator

        return {self._key: result}
