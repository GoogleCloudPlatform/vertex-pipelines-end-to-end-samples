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
# TFMA - Evaluation Metrics component

This component is used to calculate user-defined evaluation metrics of a given dataset (CSV). It uses the [`analyze_raw_data`](https://www.tensorflow.org/tfx/model_analysis/api_docs/python/tfma/analyze_raw_data) function to compute said evaluation metrics using the [TensorFlow Model Analysis](https://www.tensorflow.org/tfx/model_analysis/get_started) (TFMA) package.

In addition to computing metrics for the overall dataset, this component can also optionally, compute metrics for slices of data. The same is enabled by usage of the [`get_metrics_for_all_slices`](https://www.tensorflow.org/tfx/model_analysis/api_docs/python/tfma/EvalResult#get_metrics_for_all_slices) method

## Usage

### Metrics for Overall dataset

When slices are not defined in the pipeline step, `evaluation_metrics_tfma` computes metrics on the overall dataset. In this scenario, the pipeline step can be defined as follows:

```
metrics_names = ["AUC", "Recall"] # Can add as many supported metrics as required

eval_metrics = calculate_eval_metrics(
    csv_file=predictions.output,
    metrics_names=json.dumps(metrics_names),
    label_column_name=label_column_name,
    pred_column_name=pred_column_name,
).set_display_name("Evaluate test metrics for model")
```

The same setup can be used for computing evaluation metrics of both champion (`champion_eval_metrics`) & challenger (`challenger_eval_metrics`) models

List of metrics supported by TFMA - [`here`](https://www.tensorflow.org/tfx/model_analysis/api_docs/python/tfma/metrics)

The final piece `set_display_name(...)` is optional - it is used to create a neater display name in the Vertex Pipelines UI.

Output of this component is stored as a GCS object w/ the following format:
```
{
    "Overall": {"auc": 0.5, "recall": 0.5}
}
```
The second output of this component is a HTML file containing the visualisations of the TFMA metrics, called `plots_overall.html`.
### Metrics for Slices of dataset

When slices are defined in the pipeline step `evaluation_metrics_tfma` computes metrics on the overall dataset + on the defined slices. In this scenario, the pipeline step can be defined as follows:

```
metrics_names = ["AUC", "Recall"] # Can add as many supported metrics as required

eval_metrics = calculate_eval_metrics(
        csv_file=predictions.output,
        metrics_names=json.dumps(metrics_names),
        label_column_name=label_column_name,
        pred_column_name=pred_column_name,
        slicing_specs=[
            'feature_keys: ["feat1"]',
            'feature_keys: ["feat1", "feat2"]',
            'feature_values: [{key: "feat1", value: "abc"}]',
        ],
    ).set_display_name("Evaluate test metrics for model")
```

The same setup can be used for computing evaluation metrics of both champion (`champion_eval_metrics`) & challenger (`challenger_eval_metrics`) models

List of metrics supported by TFMA - [`here`](https://www.tensorflow.org/tfx/model_analysis/api_docs/python/tfma/metrics)

The final piece `set_display_name(...)` is optional - it is used to create a neater display name in the Vertex Pipelines UI.

With the `slicing_spec` defined in this scenario,

- `'feature_keys: ["feat1"]'` computes metrics for every distinct value in `feat1`
- `'feature_keys: ["feat1", "feat2"]'` computes metrics for every distinct combination of `feat1` + `feat2`
- `'feature_values: [{key: "feat1", value: "abc"}]'` computes metrics only when `feat1` has a value of `abc`

Output of this component is stored as a GCS object w/ the following format:
```
{
    "Overall": {"auc": 0.5, "recall": 0.5},
    # Slices for feature_keys: ["feat1"]
    ("feat1", "a"): {"auc": 0.5, "recall": 0.5},
    ("feat1", "b"): {"auc": 0.5, "recall": 0.5},
    .....
    # Slices for feature_keys: ["feat1", "feat2"]
    (("feat1", "a"), ("feat2", "x")): {"auc": 0.5, "recall": 0.5},
    (("feat1", "a"), ("feat2", "y")): {"auc": 0.5, "recall": 0.5},
    (("feat1", "b"), ("feat2", "x")): {"auc": 0.5, "recall": 0.5},
    .....
    # Slices for feature_keys: feature_values: [{key: "feat1", value: "abc"}]
    ("feat1", "abc"): {"auc": 0.5, "recall": 0.5},
}
```

For more details on `slicing_specs`, please refer to this [`link`](https://www.tensorflow.org/tfx/model_analysis/setup#slicing_specs)

This component will also output a HTML file for every slicing type specified in `slicing_spec`. In the example above, three HTML files will be created, as follows:
1. `feature_keys: ["feat1"]` will show the metrics for all of the different `feat1` values available. The output name would be `plots_feat1.html`
2. `feature_keys: ["feat1", "feat2"]` will show the metrics for every unique combination of `feat1` and `feat2` values available. The output name would be `plots_feat1_&_feat2.html`
3. `feature_values: [{key: "feat1", value: "abc"}]` will show the metrics only for the cases where the `feat1` is `abc`. The output name would be `plots_feat1_-->_abc.html`
## Creating Custom TFMA Evaluation Metrics

If the pre-existing metrics are not sufficient for your use case, TFMA also supports the definition of custom evaluation metrics. Note that there are two different ways of creating these metrics, depending on the version of TFMA used. This guide will detail how to compute these metrics for TFMA=0.37, which is the version used in the metrics. For version 1.x of TFMA, please refer to TFMA’s documentation.

### Requirements

The following package versions are required to follow this guide:
* `Tensorflow_model_analysis == 0.37.0`
* `Apache_beam == 2.35.0`
* `Protobuf == 3.18.0`
* `Python == 3.7`

This guide will show how to modify the template code to create a custom metric. Four main changes must be done to the templates (creating the custom metric script, saving the script as part of the assets, modifying the TFMA evaluation component and modifying the main pipeline script). These will be thoroughly described in the next sections:
### 1. Create module with custom metric

This is detailed in [this other guide](https://github.com/teamdatatonic/kfp-template-0/blob/feature/tfma_custom_metric/pipelines/kfp_components/evaluation/tfma_custom_metrics.md). Please follow this guide before continuing.

### 2. Add module script to `assets`

In order for TFMA to be able to use the custom metrics, they must be converted into a module, and this module must be available to TFMA at evaluation time. When running TFMA locally, and not as part of a Vertex AI pipeline, as long as the module is available locally, TFMA will be able to find it. 

However, when running a Vertex AI pipeline, each pipeline component will be running in a specified container in the Cloud, each of them independent of each other. Therefore, the custom metric module must be made available to the container which will run the pipeline code. This can be done in several ways:

1. Create a Docker image which includes the custom metric module as well as the other necessary packages and files, and use this image to initialize the container
    
2. Upload the module from the local computer into a GCS bucket. Then initialise the container with the base Python image. Within the component code, load the modules from the GCS bucket previously specified into the local container. 

The second option was used for this template. To achieve this, the first task is to “upload the module from the local computer into a GCS bucket”. The “kfp-template” code already downloads everything inside the `training.assets`, for instance under `training/assets/tfma_custom_metrics`, to a GCS bucket specified in the payload file. Therefore, to upload the modules, they need to be placed in the `assets` folder too, and the code will then automatically upload the files. Custom metrics will be used only in the training pipeline, in order to evaluate both the champion and challenger models. Therefore, the custom metrics must be added only to the training assets. 

### 3. Modify metric component source code (`evaluation_metrics_tfma.py`)

This modifications have already been imolemented as part of the code, so please continue reading. 

### 4. Modify `pipeline.py`

There are three main steps to follow when including the custom metric in the `pipeline.py` script, which are as follows:

#### 1. Create and define the custom metric variable

When defining the pipeline variables (which are currently hard-coded within the pipeline definition) an additional variable, namely `custom_metrics`, must be filled in as follows:
```
custom_metrics =  {
    “class_name_1”:”<path.to.module.1>”, 
    “class_name_2”:”<path.to.module.2>”
    }
```
For example, if a class called `SquaredPearson` had been created and saved in `squared_pearson.py` inside the `assets` folder, then `custom_metrics = {"SquaredPearson": "squared_pearson"}`

#### 2. Define the path to the GCS bucket with the custom metric modules

A new variable, called `tfma_custom_metrics_path` must be defined. This variable point to the path where the custom metric modules are stored in GCS. By default, this is saved at: 
```
tfma_custom_metrics_path = (
           f"{pipeline_files_gcs_path}/training/assets/tfma_custom_metrics/"
       )
```
but it may be changed if needed. In the template, the custom metrics were saved inside a folder named `tfma_custom_metrics` under the `assets` folder in the `training` section, hence the path selected. 

## Unit Testing Custom Metrics
When a new custom metric is created, it must be tested before being used in production. The file called `test_custom_eval_metrics.py` under the `tests/kfp_components/evaluation/` path does exactly so. When testing the custom metric, three variables are needed: 
* `MODULE_TO_TEST`: Refers to the name given to the module, without the `.py` termination. For instance, in this example this would be simply `squared_pearson`. 
* `CLASS_TO_TEST`: Refers to the name given to the class inside the module when the class is defined, such as `class CustomMetric`. In this example it would be `SquaredPearson`. 
* `CLASS_NAME_TO_TEST`: Refers to the name given to the class at the beginning of the module, before creating the class, under the variable `CUSTOM_METRIC_NAME`. In this example, it would be `squared_pearson_correlation`
<EOF>
