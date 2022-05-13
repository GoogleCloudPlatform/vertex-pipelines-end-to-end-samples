<!-- 
Copyright 2022 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
 -->
# Create TFMA Custom Metric

This document will show how to create a TFMA custom metric module. To modify the pipeline in order to include the newly created custom metric as part of the evaluation, please follow [this guide](https://github.com/teamdatatonic/kfp-template-0/blob/feature/tfma_custom_metric/pipelines/kfp_components/evaluation/evaluation_metrics_tfma.md).

If the pre-existing metrics are not sufficient for your use case, TFMA also supports the definition of custom evaluation metrics. Note that there are two different ways of creating these metrics, depending on the version of TFMA used. This guide will detail how to compute these metrics for TFMA=0.37, which is the version used in the metrics. For version 1.x of TFMA, please refer to [TFMA’s documentation](https://www.tensorflow.org/tfx/model_analysis/post_export_metrics).
## Requirements
The following package versions are required to follow this guide:
* `Tensorflow_model_analysis == 0.37.0`
* `Apache_beam == 2.35.0`
* `Protobuf == 3.18.0`
* `Python == 3.7`

To create a custom TFMA, the `tfma.metrics.Metric` must be extended. The TFMA metric consists of a Python module and is made up of four (or five if a custom preprocessor is used) main blocks, which will be shown below. The classes and methods that form the module follow the next order:
1. Import necessary packages
2. Define the main `tfma.metrics.Metric` class
3. Define the main metric function
4. Define the custom metric `Accumulator`
5. Define the custom metric `Combiner`
    1. Initialise the class (`def __init__`)
    2. Create the accumulator (`def create_accumulator`)
    3. Add the inputs of every example to the accumulator (`def add_input`)
    4. Merge all accumulators together (`def merge_accumulators`)
    5. Extract the final output (`def extract_output`)

This guide will go through all these items in detail. 

## Import necessary packages

```
from tensorflow_model_analysis.metrics import metric_types
from tensorflow_model_analysis.metrics import metric_util
from tensorflow_model_analysis.proto import config_pb2
from typing import Dict, Iterable, Optional
import apache_beam as beam
```
TFMA contains some very useful scripts to aid in the creation of custom metrics (found in `metric_types` and `metric_util`). Apache Beam is used to compute the actual metric values, so it must be imported too. 

## Define the main metric Class

Create a metric class (in this case called `CustomMetric`) which extends from `tfma.metrics.Metric`. This class simply sets the name of the metric, and then calls the main metric function (named `_custom_metric_fn`). Then, a very important step is to register the newly created custom metric as part of the TFMA metric register. In this way, when the metric is called, TFMA will look for a metric that is called as such. 
```
# First you need to provide the custom metric name
CUSTOM_METRIC_NAME = "my_custom_metric"
 
# Then you need to initialise the custom metric class, which will simply call the custom metric function created later
class CustomMetric(metric_types.Metric):
   def __init__(self, name: str = CUSTOM_METRIC_NAME):
       """Initializes custom metric.
       Args:
           name (str): Metric name.
       """
       super().__init__(
           metric_util.merge_per_key_computations(_custom_metric_fn),
           name=name)
 
# Then you need to register your custom metric in the TFMA metric register
metric_types.register_metric(CustomMetric)
```

## Define the metric main function

As shown above, the metric main class simply calls a function. This function must then be defined as below:
```
# Create the custom metric function that runs the custom metric pre-processor and combiner
def _custom_metric_fn(
   name: str = CUSTOM_METRIC_NAME,
   eval_config: Optional[config_pb2.EvalConfig] = None,
   model_name: str = '',
   output_name: str = '',
   sub_key: Optional[metric_types.SubKey] = None,
   aggregation_type: Optional[metric_types.AggregationType] = None,
   class_weights: Optional[Dict[int, float]] = None,
   example_weighted: bool = False) -> metric_types.MetricComputations:
 """Returns metric computations for the custom metric.
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
     example_weighted=example_weighted)
 
 return [
     metric_types.MetricComputation(
         keys=[key],
         preprocessor=None, # pre-processes the data. If not defined, it will output (label, prediction, weight) for every example
         combiner=_CustomMetricCombiner(key, eval_config,
                                                     aggregation_type,
                                                     class_weights,
                                                     example_weighted))
 ]

```
This function returns a `tfma.metrics.MetricComputation` object which essentially defines the computations that must be performed to obtain the metric. The function that creates these computations will be passed the following parameters as input:

* `eval_config`: `tfma.EvalConfig`
  * The eval config passed to the evaluator (useful for looking up model spec settings such as prediction key to use, etc).
* `model_names`: `List[Text]`
  * List of model names to compute metrics for (None if single-model)
* `output_names`: `List[Text]`
  * List of output names to compute metrics for (None if single-model)
* `sub_keys`: `List[tfma.SubKey]`
  * List of sub keys (class ID, k or top K) to compute metrics for (or None). The sub keys refer to the label column. If specifying a sub key, only one of the three types (class ID, k or top_K) can be used. Class ID can only be used for classification purposes.
* `aggregation_type`: `tfma.AggregationType`
  * Type of aggregation if computing an aggregation metric.
* `class_weights`: `Dict[int, float]`
  * Class weights to use if computing an aggregation metric.

As detailed above, this function returns a `tfma.metrics.MetricComputation`. This describes what sort of computations must be done to obtain the metric. A metric computation is made up of a `preprocessor` and a `combiner`. The preprocessor is a `beam.DoFn` that takes extracts as its input and outputs the initial state that will be used by the combiner (see [architecture](https://www.tensorflow.org/tfx/model_analysis/architecture) for more info on what are extracts). If a preprocessor is not defined, then the combiner will be passed `StandardMetricInputs` (standard metric inputs contains `labels`, `predictions`, and `example_weights`). The combiner is a `beam.CombineFn` that takes a tuple of (slice key, preprocessor output) as its input and outputs a tuple of (slice_key, metric results dict) as its result.
 
In the example above, no `preprocessor` is specified, only the `combiner`. Therefore, the next task is to create the custom metric combiner. However, before doing so, an `accumulator` must be created. To give some insight into why, it is important to understand how TFMA calculates metrics. TFMA is simply running various Apache Beam pipelines under the hood. These pipelines are run in parallel, using various processors. Therefore, the input data that must be evaluated is split into chunks, and the metrics of each chunk computed in parallel. Then, these metrics must be combined together again to output the final metric value. The role of the accumulator is to store the intermediate metric values for every chunk. The role of the combiner is to call the accumulator, add the metric values to the accumulator, combine the values of all accumulators together and finally provide the end result. 

## Define the custom metric Accumulator

The accumulator is simply created and initialised to 0. Here is where the different metric results will be stored. If in order to calculate a metric several different “sub-metrics” are required, this is where they should be created (for instance, the squared labels or squared predictions). 
```
# Define the Accumulator, which accumulates the metric value for different chunks of data processed by different workers
class _CustomMetricAccumulator:
   """This class simply initialises the Accumulator, which is where the metric results are saved to.
   This is called by the Combiner, which runs the metric computation for several different processors and then
   combines them together into a single metric
 
   This class is initialised with the different attributes required by the custom metric.
   An example of how this is initialised is as follows:
 
   self.total_weighted_labels = 0.0
   self.total_weighted_predictions = 0.0
   """
 
   def __init__(self) -> None:
       self.total_metric_value = 0.0
 ```
 ## Define the custom metric Combiner
 
 The `combiner` is where the metric is actually calculated, hence where all the equations should be written. The combiner consists of five methods, which will be described below:
 
 #### Initialise the class
 
 ```
 # Define the Combiner, which actually computes the metric value and combines the values for different chunks of data into the Accumulator
class _CustomMetricCombiner(beam.CombineFn):
   """Computes the custom metric and saves results into the Accumulator
  
   Initialise with any necessary attribute required during the metric computation. The package `metric_util` contains
   many methods that are useful in order to compute metrics. Please refer to the documentation for further details
   https://github.com/tensorflow/model-analysis/blob/v0.37.0/tensorflow_model_analysis/metrics/metric_util.py
  
   An example of how this is initialised is as follows:
   def __init__(self, key: metric_types.MetricKey,
              eval_config: Optional[config_pb2.EvalConfig],
              aggregation_type: Optional[metric_types.AggregationType],
              class_weights: Optional[Dict[int,
                                           float]], example_weighted: bool):
       self._key = key
       self._eval_config = eval_config
       self._aggregation_type = aggregation_type
       self._class_weights = class_weights
       self._example_weighted = example_weighted

  Args:
    key (MetricKey): Metric key used in the evaluation
    eval_config (EvalConfig): Configuration of evaluation job used by Beam
    aggregation_type (AggregationType): If any aggregation is used, specify which
            type
    class_weights (dict): Different weights applied to classes during classification
    example_weighted (bool): Specify if extra weight needs to be applied to
            any example
   """
 
   def __init__(self):
       self._metric_attributes = None
```
First, initialize the class. This must be done by initialising the different attributes that are required during the computation (for instance key, eval_config, etc). 

#### Create the accumulator

```
def create_accumulator(self) -> _CustomMetricAccumulator:
       """Initialises an empty accumulator"""
       return _CustomMetricAccumulator()
```
Then you must initialize the accumulator which was created in the previous step

#### Add the inputs of every example to the accumulator

```
def add_input(
       self,
       accumulator: _CustomMetricAccumulator,
       element # If preprocessor=None in _custom_metric_fn this will be a metric_types.StandardMetricInputs
       )-> _CustomMetricAccumulator:
       """This is where the value of the metric is actually compute
       
       Args:
            accumulator (Accumulator): Accumulator where the results will be added to
            element (StandardMetricInput): Item that contains the label that
                 needs evaluation"""
 
       for label, prediction in element.processed:
           accumulator.total_metric_value += ("""function of label and predictions""")
       return accumulator
```
In this step, the code iterates through every element of the given chunk to get the labels and predictions (and any other item if necessary → refer to [`tensorflow_model_analysis.metrics.metric_util`](https://github.com/tensorflow/model-analysis/blob/eeb80eca762fa50d17ad3eb94904de48a7a707a9/tensorflow_model_analysis/metrics/metric_util.py) for the various different possibilities), does the necessary computations to these labels and predictions (for instance, weighing them or squaring them) and adds the value to the accumulator that was previously initialised. 

#### Merge all accumulators together

```
def merge_accumulators(
       self,
       accumulators: Iterable[_CustomMetricAccumulator])-> _CustomMetricAccumulator:
       """Merge the accumulator values of different chunks of data together. Data is processed by Beam in different
       workers
       """
 
       accumulators = iter(accumulators)
       result = next(accumulators)
       for accumulator in accumulators:
           result.final_result += accumulator.total_metric_value
       return result
```
The next step is to combine all of the accumulators together. This is done by iterating through the accumulator and adding the value to a `results` variable, which is then returned by the method. 

#### Extract the final output

```
def extract_output(
       self,
       accumulator: _CustomMetricAccumulator
   )-> Dict[metric_types.MetricKey, float]:
       """Obtain final metric result. Transform accumulator value if required"""
 
       result = accumulator.final_result
 
       return {self._key: result}
```
Final transformations can be done here, once all of the accumulators have been merged together. For example, when computing the True Positive Rate, this can only be obtained once all true positives have been counted, hence the TPR would need to be calculated in this method. If this were the case, the `add_input` method would be counting the true positives, true negatives, etc, for every chunk and accumulating those in the accumulator, and the TPR would only be calculated at this point. 

## Coded example

For an example of an end-to-end custom TFMA metric, please refer to [the `assets` folder under `tensorflow/training/`](https://github.com/teamdatatonic/kfp-template-0/tree/feature/tfma_custom_metric/pipelines/tensorflow/training/assets/tfma_custom_metrics)

<EOF>
 
