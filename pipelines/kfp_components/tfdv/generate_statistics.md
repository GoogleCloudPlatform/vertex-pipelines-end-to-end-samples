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
# Generate Statistics component

This component is used to calculate statistics of a given dataset (CSV). It uses the [`generate_statistics_from_csv`](https://www.tensorflow.org/tfx/data_validation/api_docs/python/tfdv/generate_statistics_from_csv) function in the [TensorFlow Data Validation](https://www.tensorflow.org/tfx/guide/tfdv) (TFDV) package.

As well as being run in an ordinary pipeline container, it can optionally be run on [DataFlow](https://cloud.google.com/dataflow/), allowing it to scale to massive datasets.

## Usage

### Normal usage - DirectRunner

In this mode, all the computation happens with the Vertex Pipeline step. This is the approach that is used in the example ML pipelines, but of course you can easily change this to make use of DataFlow (see below).

#### Code example

The example below shows the use of a `file_pattern` for selecting a dataset spread across multiple CSV file. The `dataset` parameter uses the output from a previous pipeline step (a dataset in CSV format) - alternatively you can use the GCS path of a CSV file.

```
gen_statistics = generate_statistics(
        dataset=train_dataset.outputs["dataset"],
        file_pattern="file-*.csv",
    ).set_display_name("Generate data statistics")
```

The final piece `set_display_name(...)` is optional - it is used to create a neater display name in the Vertex Pipelines UI.

### Running on DataFlow without a prebuilt container image

In this approach, the DataFlow workers install Apache Beam and TFDV when the job runs. The benefits to this approach are mainly simplicity - you don't need to create a custom container image for the DataFlow workers to use.

The drawbacks to this approach include:

- Slower job startup, as the DataFlow workers need to install the dependencies at the start of each job
- Relies on PyPi availability at runtime

#### Code example

In this example we have additionally set the following parameters:

- `use_dataflow=True`
- `project_id` - the GCP project ID where we want to run the DataFlow job
- `region` - the GCP region where we want to run the DataFlow job
- `gcs_staging_location` - A GCS path that can be used as a DataFlow staging location
- `gcs_temp_location` - A GCS path that can be used as a DataFlow temp / scratch directory

```
gen_statistics = generate_statistics(
        dataset=train_dataset.outputs["dataset"],
        file_pattern="file-*.csv",
        use_dataflow=True,
        project_id="my-gcp-project",
        region="europe-west1",
        gcs_staging_location="gs://my-gcs-bucket/dataflow-staging",
        gcs_temp_location="gs://my-gcs-bucket/dataflow-temp",
    ).set_display_name("Generate data statistics")
```

### Running on DataFlow using a prebuilt container image

In this approach, a custom container image is used by the DataFlow workers, meaning that the DataFlow workers don't need to install anything when the job runs.

The benefits to this approach include:

- Quicker job startup (don't need to install packages each time)
- More deterministic behaviour (even if package versions are pinned, their dependencies might not be!)
- No reliance on PyPi repositories at runtime - for instance if you are operating in a disconnected environment, or if you are concerned about the public PyPi repositories experiencing an outage

The main drawback to this approach is that you need to provide a custom container image with Apache Beam and TFDV pre-installed. The next section contains more details on how you can create the custom container image.

#### Code example

In this example we have additionally set the following parameters:

- `tfdv_container_image` - the container image to use for the DataFlow runners - must have Apache Beam and TFDV preinstalled (the same versions as you use to make the function call in the pipeline step!)
- `subnetwork` - the subnetwork that you want to attach the DataFlow workers to. Should be in the form `regions/REGION_NAME/subnetworks/SUBNETWORK_NAME` - see further docs [here](https://cloud.google.com/dataflow/docs/guides/specifying-networks). Also note that the DataFlow region must match the region of the subnetwork!
- `use_public_ips=False` - we specify that the DataFlow workers should not have public IP addresses. Without additional networking considerations (a NAT gateway), this generally means that they are unable to access the internet

Of course, you can also use the `tfdv_container_image` without using the `subnetwork` and `use_public_ips` parameters, so your DataFlow workers will still have public IP addresses and will use the default compute network.

```
gen_statistics = generate_statistics(
        dataset=train_dataset.outputs["dataset"],
        file_pattern="file-*.csv",
        use_dataflow=True,
        project_id="my-gcp-project",
        region="europe-west1",
        gcs_staging_location="gs://my-gcs-bucket/dataflow-staging",
        gcs_temp_location="gs://my-gcs-bucket/dataflow-temp",
        tfdv_container_image="eu.gcr.io/my-gcp-project/my-custom-tfdv-image:latest",
        subnetwork="regions/europe-west1/subnetworks/my-subnet",
        use_public_ips=False,
    ).set_display_name("Generate data statistics")
```

## Creating a custom container image for use with DataFlow

Creating the custom container image is very simple. Here is an example of a Dockerfile that you can use:

```
# Use correct image for Apache Beam version
FROM apache/beam_python3.7_sdk:2.35.0

# Install TFDV on top 
RUN pip install tensorflow-data-validation==1.6.0

# Check version compatibilities here
# https://www.tensorflow.org/tfx/data_validation/install#compatible_versions
```

## Additional component parameters

In the docstring for the [`generate_statistics`](generate_statistics.py) component, you will notice a few other parameters that we haven't mentioned in the examples above:

- `statistics` - this is the output path that the statistics file is written to. Since its type is `Output[Artifact]`, Vertex Pipelines automatically provides the path for us without us having to specify it

The following options are all related to the Apache Beam `PipelineOptions`. Each is a dictionary that you can pass to the component to construct the `PipelineOptions`. Any options passed in using these dictionaries will override those set by the component (as these dictionaries are applied last), so use with care! You can find more details about how to set the `PipelineOptions` in the [Apache Beam](https://beam.apache.org/releases/pydoc/current/_modules/apache_beam/options/pipeline_options.html) and [DataFlow](https://cloud.google.com/dataflow/docs/guides/setting-pipeline-options) documentation.

- `extra_standard_options`
- `extra_setup_optons`
- `extra_worker_options`
- `extra_google_cloud_options`
- `extra_debug_options`

In addition to these options, you can also pass options required for generating statistics with `tfdv_stats_options`. For example, these stats options can include (but are not limited to):

- `schema`: Pre-defined schema as a `tensorflow_metadata` Schema proto
- `infer_type_from_schema`: Boolean to indicate whether the feature types should be inferred from a schema
- `feature_allowlist`: List of feature names to calculate statistics for
- `sample_rate`
- `desired_batch_size`

For more details, please refer to this [link](https://www.tensorflow.org/tfx/data_validation/api_docs/python/tfdv/StatsOptions).
