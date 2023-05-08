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
# TensorFlow Pipelines

## Training pipeline
The TensorFlow training pipeline can be found in [`training/pipeline.py`](training/pipeline.py). The training component [`train_tensorflow_model`](../../../pipeline_components/_tensorflow/_tensorflow/train/component.py) is the main training component which contains the implementation of a TensorFlow Keras model.
This component can then be wrapped in a custom kfp ContainerOp from [`google-cloud-pipeline-components`](https://github.com/kubeflow/pipelines/blob/master/components/google-cloud/google_cloud_pipeline_components/experimental/custom_job/utils.py) which submits a Vertex Training job with added flexibility for `machine_type`, `replica_count`, `accelerator_type` among other machine configurations. 

### Data
The input data is split into three parts in BigQuery and stored in Google Cloud Storage: 
- 80% of the input data is used for model training
- 10% of the input data is used for model validation
- 10% of the input data is used for model testing/evaluation

### Model Architecture
The architecture of the example TensorFlow Keras model is shown below:

![TensorFlow Model Architecture](../../docs/images/tf_model_architecture.png)

- **Input layer**: there is one input node for each of the 7 features used in the example:
    - `dayofweek`
    - `hourofday`
    - `trip_distance`
    - `trip_miles`
    - `trip_seconds`
    - `payment_type`
    - `company`
- **Pre-processing layers**
    - Categorical encoding for categorical features is done using Tensorflow's `StringLookup` layer. New/unknown values are handled using this layer's default parameters. (https://www.tensorflow.org/api_docs/python/tf/keras/layers/StringLookup). 
        - The feature `payment_type` is one-hot encoded. New/unknown categories are assigned to a one-hot encoded array with zeroes everywhere. 
        - The feature `company` is ordinal encoded. New/unknown categories are assigned to zero.  
    - Normalization for the numerical features (`dayofweek`, `hourofday`, `trip_distance`, `trip_miles`, `trip_seconds`)
- **Dense layers**
    - One `Dense` layer with 64 units whose activation function is ReLU. 
    - One `Dense` layer with 32 units whose activation function is ReLU.
- **Output layer**
    - One `Dense` layer with 1 unit where no activation is applied (this is because the example is a regression problem)


### Model hyperparameters
You can specify different hyperparameters through the `model_params` argument of `train_tensorflow_model`, including:
- Batch size
- No. of epochs to check for early stopping
- Learning rate
- Number of hidden units and type of activation function in each layer
- Loss function
- Optimization method
- Evaluation metrics
- Whether you want early stopping

For a comprehensive list of options for the above hyperparameters, see the docstring in [`train.py`](../../../pipeline_components/_tensorflow/_tensorflow/train/component.py). 

### Model artifacts
A number of different model artifacts/objects are created by the training of the TensorFlow model. With these files, you can load the model into a new script (without any of the original training code) and run it or resume training from exactly where you left off. For more information, see [this](https://www.tensorflow.org/api_docs/python/tf/keras/models/save_model). 


![tensorflow_component_model&metrics_artifact](../../docs/images/tensorflow_component_model&metrics_artifact.png)
### Model test/evaluation
Once the model is trained, it will be used to get challenger predictions for evaluation purposes. In general, the component [`predict_tensorflow_model`](../kfp_components/tensorflow/predict.py)
which expects a single CSV file to create predictions for test data is implemented in the pipeline, However, if you are working working with larger test data, it is more efficient to 
replace it with a prebuilt component provided by Google, [`ModelBatchPredictOp`](https://google-cloud-pipeline-components.readthedocs.io/en/google-cloud-pipeline-components-0.2.1/google_cloud_pipeline_components.aiplatform.html), 
to avoid crash caused by insufficent memory usage.

### Distribution strategy
In deep learning, it is common to use GPUs, which utilise a large number of simple cores allowing parallel computing though thousands of threads at a time, to train complicated neural networks fed by massive datasets.
For optimisation tasks, it is often better to use CPUs.

 There is a variable, `distribute_strategy`, in tensorflow training pipeline that allows you to set up distribution strategy. You have three options:
|Value| description |
|---|---|
|`single` | This strategy use GPU is a GPU device of the requested kind is available, otherwise, it uses CPU |
|`mirror` | This strategy is typically used for training on one machine with multiple GPUs. |
|`multi`|This strategy implements synchronous distributed training across multiple machines, each with potentially multiple GPUs|

## Prediction pipeline
The TensorFlow prediction pipeline can be found in [prediction/pipeline.py](prediction/pipeline.py). 
