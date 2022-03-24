from kfp.v2.dsl import Dataset, Input, Output, Artifact, component, HTML
from pipelines.kfp_components.dependencies import (
    PYTHON37,
    TENSORFLOW_MODEL_ANALYSIS,
    PANDAS,
    PROTOBUF,
    GOOGLE_CLOUD_STORAGE,
)


@component(
    base_image=PYTHON37,
    packages_to_install=[
        TENSORFLOW_MODEL_ANALYSIS,
        PANDAS,
        PROTOBUF,
        GOOGLE_CLOUD_STORAGE,
    ],
)
def calculate_eval_metrics(
    csv_file: Input[Dataset],
    metrics_names: list,
    label_column_name: str,
    pred_column_name: str,
    eval_metrics: Output[Artifact],
    view: Output[HTML],
    project_id: str = None,
    custom_metrics: dict = None,
    custom_metrics_path: str = None,
    slicing_specs: list = None,
) -> None:
    """
    Compute evaluation metrics based on actual and predicted labels.

    Args:
        csv_file (Input[Dataset]): Dataset with the actual labels and predicted labels
            in CSV format
        metrics_names (str): string with comma-separated metric names. See available
            metrics in TFMA documentation:
            https://www.tensorflow.org/tfx/model_analysis/metrics
        label_column_name (str): name of column containing actual labels
        pred_column_name (str): name of column containing predicted labels
        eval_metrics (Output[Artifact]): Output evaluation metrics of the model
        view (Output[Artifact]): Output artifact to store the visualised statistics
            as a html file.
        project_id (str): Google Cloud project ID (for use with TFMA)
        custom_metrics (dict): Dictionary containing custom metrics used in
            the evaluation. The format is as follows:
            {
                "custom_metric_name_1":"<path.to.module.1>",
                "custom_metric_name_2":"<path.to.module.2>"
            }
        custom_metrics_path (str): Path to GCS location where the custom metric
            modules are located
        slicing_specs (list): list of slicing specs where each spec in the list is
            a str. Expected formats of slicing_specs as follows:
            1) 'feature_keys: ["feat1"]'
            2) 'feature_keys: ["feat1", "feat2"]'
            3) 'feature_values: [{key: "feat1", value: "abc"}]
            4) 'feature_keys: ["feat1"] feature_values: [{key: "feat2", value: "abc"}]
            Reference: https://www.tensorflow.org/tfx/model_analysis/setup#slicing_specs

    Returns:
        None.
    """
    import json
    import logging
    import pandas as pd
    from google.protobuf import text_format
    import tensorflow_model_analysis as tfma
    from google.cloud import storage
    from ipywidgets.embed import embed_minimal_html
    import codecs
    from tensorflow_model_analysis.view import render_slicing_metrics

    # Define helper functions for metric visualisations
    def get_feature_keys(keys_string):
        """String manipulation to obtain all feature keys from a single slicing
            specification returned as a single list

        Args:
            keys_string (str): String containing the feature keys. This string
            has the following naming convention:
                'feature_keys: ["<feature_one>", "<feature_two>"]'
            The string manipulation aims to obtain all of the <feature_XX> keys
            in a single list

        Returns:
            feature_keys (list): List containing all feature keys in the given slice
        """

        feature_keys = []  # Initialise empty list

        # Get all keys as list of string
        """
        Need to convert string 'feature_keys: ["<feature_one>", "<feature_two>"]'
        into list of strings ["<feature_one>", "<feature_two>"]
        """
        keys_list = (
            keys_string.split("feature_keys:")[1]
            .lstrip()
            .split("[")[1]
            .split("]")[0]
            .split(",")
        )

        # Clean every string item in list
        for onekey in keys_list:
            keyname = onekey.replace('"', "").replace("'", "").strip()
            feature_keys.append(keyname)

        return feature_keys

    def get_key_value_pair(key_value_string):
        """String manipulation to obtain the key-value pair from the slicing
            specification. Currently TFMA only supports having a single key-value
            pair as part of a slicing specification. If this changes, this
            function must also change.

        Args:
            key_value_string (str): String containing the key-value pair. This string
                has the following naming convention:
                'feature_keys: ["<feature_key>"]
                    feature_values: [{key: "<key>", value: "<value>"}]'
                The string manipulation aims to obtain the <key> and <value> names.

        Returns:
            key (str): Key name given in slicing spec.
            value (str): Value name given in slicing spec.
        """

        # Get key name
        key = (
            key_value_string.split("key:")[1]
            .split(",")[0]
            .replace('"', "")
            .replace("'", "")
            .strip()
        )

        # Get value name
        value = (
            key_value_string.split("value:")[1]
            .split("}")[0]
            .replace('"', "")
            .replace("'", "")
            .strip()
        )
        return key, value

    def save_html_visualisation(plot_name: str, view: Output[Artifact]):
        """Reads in HTML file and saves it in GCS with a unique name

        Args:
            plot_name (str): Name given to html file with visualisation. Must be of
                the format <name_given_to_plot>.html
            view (Output[Artifact]): Output artifact to store the visualised statistics
            as html file.
        """

        # Read HTML file as string
        f = codecs.open(plot_name, "r")
        text_html = f.read()

        # Ensure view is stored as html (this will set content-type to text/html)
        if not view.path.endswith(".html"):
            view.path += ".html"

        # Replace existing HTML with unique plot name to ensure all plots are saved
        current_name = view.path.split("/")[-1]
        view.path = view.path.replace(current_name, plot_name)

        # Write html to output file
        with open(view.path, "w") as f:
            f.write(text_html)

    # Download package from GCS if custom metrics are specified
    if custom_metrics:
        storage_client = storage.Client(project=project_id)
        for custom_metric in custom_metrics.values():
            with open(f"{custom_metric}.py", "wb") as fp:
                storage_client.download_blob_to_file(
                    f"{custom_metrics_path}/{custom_metric}.py", fp
                )

    #################################################
    logging.getLogger().setLevel(logging.INFO)

    # Read labels (actual and predicted) and metrics names into dataframes
    df = pd.read_csv(csv_file.path)

    # Generate protobuf (required by TFMA) specifying evaluation metrics to calculate
    metrics_specs = ""
    for metric in metrics_names:
        metrics_specs += f'metrics {{ class_name: "{metric}" }}\n'

    # Adding custom metrics if specified
    if custom_metrics:
        for class_name, module_name in custom_metrics.items():
            metric_spec = f' {{ class_name: "{class_name}" module: "{module_name}" }}'
            metrics_specs += f"metrics {metric_spec}\n"

    slicing_spec_proto = "slicing_specs {}\n"
    if slicing_specs:
        for single_slice in slicing_specs:
            slicing_spec_proto += f"slicing_specs {{ {single_slice} }}\n"

    protobuf = """
                ## Model information
                model_specs {{
                    label_key: "{0}"
                    prediction_key: "{1}"
                }}
                ## Post export metric information
                metrics_specs {{
                    {2}
                }}
                ## Slicing information inc. overall
                {3}
                """

    eval_config = text_format.Parse(
        protobuf.format(
            label_column_name, pred_column_name, metrics_specs, slicing_spec_proto
        ),
        tfma.EvalConfig(),
    )

    # Calculate evaluation metrics
    eval_result = tfma.analyze_raw_data(df, eval_config=eval_config)

    # Get metric names and values for all slices defined (inc overall)
    evaluation = eval_result.get_metrics_for_all_slices()

    # Plot TFMA metrics for every slicing
    if slicing_specs:
        for onespec in slicing_specs:
            """
            Depending on the type of slice, a different pre-processing must be done
            """
            # If only feature keys are specified
            if "feature_keys:" in onespec and "feature_values: " not in onespec:

                # Get all keys as list of strings
                spec_keys = get_feature_keys(onespec)

                # Define slice for metrics
                specs = tfma.SlicingSpec(feature_keys=spec_keys)

                # Render metrics
                plots_tfma = render_slicing_metrics(eval_result, slicing_spec=specs)
                html_name = f'plots_{"_&_".join(spec_keys)}.html'

            # If only feature values are specified
            elif "feature_values: " in onespec and "feature_keys:" not in onespec:

                # Get key-value pair names
                keyname, valname = get_key_value_pair(onespec)

                # Define slice for metrics
                specs = tfma.SlicingSpec(feature_values={keyname: valname})

                # Render metrics
                plots_tfma = render_slicing_metrics(eval_result, slicing_spec=specs)
                html_name = f"plots_{keyname}_-->_{valname}.html"

            # If a combination of feature keys and feature values are specified
            elif "feature_keys:" in onespec and "feature_values: " in onespec:

                # Get key-value pair names
                keyname, valname = get_key_value_pair(onespec)

                # Get all feature keys as list of strings
                spec_keys = get_feature_keys(onespec)

                # Define slice for metrics
                specs = tfma.SlicingSpec(
                    feature_keys=spec_keys, feature_values={keyname: valname}
                )

                # Render metrics
                plots_tfma = render_slicing_metrics(eval_result, slicing_spec=specs)
                html_name = (
                    f'plots_{"_&_".join(spec_keys)}_<>_{keyname}_-->_{valname}.html'
                )

            # Save plot in GCS
            embed_minimal_html(html_name, views=[plots_tfma])
            save_html_visualisation(html_name, view)

    # Create a final plot without any slice, just for the overall metric
    plots_tfma = render_slicing_metrics(eval_result)
    html_name = "plots_overall.html"
    embed_minimal_html(html_name, views=[plots_tfma])  # Render
    save_html_visualisation(html_name, view)  # Save to GCS

    # Loop through all slices & metrics for each slice
    metrics_dict = {}
    for slice_spec, metrics in evaluation.items():
        logging.info(f"Extract {metrics.keys()} for {slice_spec}")
        slice_name = "Overall" if not slice_spec else slice_spec
        metric_vals = {
            metric_name: metric_val["doubleValue"]
            for metric_name, metric_val in metrics.items()
        }
        # Save metric name & value
        metrics_dict[slice_name] = metric_vals

    # Save keys as str since tuple keys cannot be parsed by json
    with open(eval_metrics.path, "w") as f:
        json.dump({str(k): v for k, v in metrics_dict.items()}, f)
