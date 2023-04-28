# XGBoost Pipelines

## Training pipeline 

The XGBoost training pipeline can be found in [`training/pipeline.py`](training/pipeline.py) . Within the kubeflow pipeline, [`train_xgboost_model`](../kfp_components/xgboost/train.py) is the main training component which contains the implementation of an XGB model with `scikit-learn` preprocessing.This component can then be wrapped in a custom kfp ContainerOp from [`google-cloud-pipeline-components`](https://github.com/kubeflow/pipelines/blob/master/components/google-cloud/google_cloud_pipeline_components/experimental/custom_job/utils.py) which submits a Vertex Training job with added flexibility for `machine_type`, `replica_count`, `accelerator_type` among other machine configurations.

The training phase is preceded by a preprocessing phase where different transformations are applied to the training and evaluation data using scikit-learn preprocessing functions. The **preprocessing** step and the **training** step define the two components of the Scikit-Learn pipeline as shown in the diagram below.

![Training process](../../docs/images/xgboost_architecture.png)

## Preprocessing with Scikit-learn
The 3 data transformation steps considered in the `train.py` script are:

|Encoder|Description|Features|
|:----|:----|:----|
|[StandardScaler()](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)|Centering and scaling numerical values|   `dayofweek`, `hourofday`, `trip_distance`, `trip_miles`, `trip_seconds`|
|[OneHotEncoder()](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html)|Encoding a chosen subset of categorical features as a one-hot numeric array|`payment_type`, new/unknown values in categorial features are represented as zeroes everywhere in the one-hot numeric array|
|[OrdinalEncoder()](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OrdinalEncoder.html)|Encoding a chosen subset of categorical features as an integer array|`company`, new/unknown values in categorical features are assigned to an integer equal to the number of categories for that feature in the training set|

More processing steps can be included to the pipeline. For more details, see the [official documentation](https://scikit-learn.org/stable/modules/preprocessing.html). Ensure that these additional pre-processing steps can handle new/unknown values in test data.

## The XGBoost Model

In our example implementation, we have a regression problem of predicting the total fare of a taxi trip in Chicago. Thus, we use XGBRegressor whose hyperparameteres are defined in the variable `model_params` in the file [training/pipeline.py](training/pipeline.py).

### Model Hyperparameters

You can specify different hyperparameters through the `model_params` argument of `train_xgboost_model`, including:
  - `Booster`: the type of booster (`gbtree` is a tree based booster used by default).
  - `max_depth`: the depth of each tree.
  - `Objective`: equivalent to the loss function (squared loss, `reg:squarederror`, is the default).
  - `min_split_loss`: the minimum loss reduction required to make a further partition on a leaf node of the tree.

More hyperparameters can be used to customize your training. For more details consult the [XGBoost documentation](https://xgboost.readthedocs.io/en/stable/parameter.html)

### Model artifacts
Two model artifacts are generated when we run the training job: 
  - `Model.joblib` : The model is exported to GCS file as a [joblib](https://joblib.readthedocs.io/en/latest/why.html#benefits-of-pipelines) object.
  - `Eval_result` : The evaluation metrics are exported to GCS as JSON file.

![xgboost_component_model&metrics_artifact](../../docs/images/xgboost_component_model&metrics_artifact.png)
### Model test/evaluation
Once the model is trained, it will be used to get challenger predictions for evaluation purposes. In general, the component [`predict_tensorflow_model`](../kfp_components/tensorflow/predict.py)
which expects a single CSV file to create predictions for test data is implemented in the pipeline. However, if you are working with larger test data, it is more efficient to 
replace it with a Google prebuilt component, [`ModelBatchPredictOp`](https://google-cloud-pipeline-components.readthedocs.io/en/google-cloud-pipeline-components-0.2.1/google_cloud_pipeline_components.aiplatform.html), 
to avoid crash caused by memory overload.

## Prediction pipeline
The XGBoost prediction pipeline can be found in [prediction/pipeline.py](prediction/pipeline.py). 
