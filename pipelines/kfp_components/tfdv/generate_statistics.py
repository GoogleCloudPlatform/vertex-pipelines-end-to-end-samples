from kfp.v2.dsl import Input, Dataset, Output, Artifact, component
from pipelines.kfp_components.dependencies import (
    PYTHON37,
    TENSORFLOW_DATA_VALIDATION,
    APACHE_BEAM,
)


@component(
    base_image=PYTHON37, packages_to_install=[TENSORFLOW_DATA_VALIDATION, APACHE_BEAM]
)
def generate_statistics(
    statistics: Output[Artifact],
    dataset: Input[Dataset],
    use_dataflow: bool = False,
    project_id: str = None,
    region: str = None,
    subnetwork: str = None,
    use_public_ips: bool = True,
    tfdv_container_image: str = None,
    gcs_staging_location: str = None,
    gcs_temp_location: str = None,
    extra_standard_options: dict = {},
    extra_setup_options: dict = {},
    extra_worker_options: dict = {},
    extra_google_cloud_options: dict = {},
    extra_debug_options: dict = {},
    file_pattern: str = None,
    tfdv_stats_options: dict = None,
) -> None:
    """
    Generate tfdv statistics given a Dataset as input.
    Wraps tfdv.generate_statistics function.

        Args:
            statistics (Output[Artifact]): this parameter will be passed
                automatically by the KFP orchestrator at runtime.
            dataset (Input[Dataset]): the desired Input[Dataset] from which the
                statistics will need to be generated.
            use_dataflow (bool): whether to run the job using Dataflow
                instead of locally. Defaults to False.
            project_id (str): Google Cloud project ID (for use with Dataflow)
            region (str): Region in which to run the Dataflow job
            subnetwork (str): Subnetwork in which to run the Dataflow job,
                in the form regions/<REGION>/subnetworks/<SUBNET_NAME>.
                Dataflow uses the project default network by default.
            use_public_ips (bool): Whether the Dataflow worker nodes should have
                public IP addresses. Defaults to True.
            tfdv_container_image (str): URI of a container image to use for the
                Dataflow workers. It should be based on the appropriate Apache Beam
                base image (Python 3.7, >=v2.35.0), and should have TFDV preinstalled
                (same version as is used here). An example Dockerfile can be found in
                this repo under containers/tfdv. If not provided, Dataflow will install
                from PyPi.
            gcs_staging_location (str): GCS path for a Dataflow staging location.
            gcs_temp_location (str): GCS path for a Dataflow temp/scratch location.
            extra_standard_options (dict): any extra StandardOptions you want to use for
                the Beam job. Note that these are applied last, so may overwrite any of
                the settings applied by this function. See the reference here:
                https://beam.apache.org/releases/pydoc/current/_modules/apache_beam/options/pipeline_options.html#StandardOptions
            extra_setup_options (dict): any extra SetupOptions you want to use for the
                Beam job. Note that these are applied last, so may overwrite any of the
                settings applied by this function. See the reference here:
                https://beam.apache.org/releases/pydoc/current/_modules/apache_beam/options/pipeline_options.html#SetupOptions
            extra_worker_options (dict): any extra WorkerOptions you want to use for the
                Beam job. Note that these are applied last, so may overwrite any of the
                settings applied by this function. See the reference here:
                https://beam.apache.org/releases/pydoc/current/_modules/apache_beam/options/pipeline_options.html#WorkerOptions
            extra_google_cloud_options (dict): any extra GoogleCloudOptions you want to
                use for the Beam job. Note that these are applied last, so may overwrite
                any of the settings applied by this function. See the reference here:
                https://beam.apache.org/releases/pydoc/current/_modules/apache_beam/options/pipeline_options.html#GoogleCloudOptions
            extra_debug_options (dict): any extra DebugOptions you want to use for the
                Beam job. Note that these are applied last, so may overwrite any of the
                settings applied by this function. See the reference here:
                https://beam.apache.org/releases/pydoc/current/_modules/apache_beam/options/pipeline_options.html#DebugOptions
            file_pattern (str): Read data from one or more files. If empty, then
                input data is read from single file. For multiple files, use a pattern
                e.g. "file-*.csv".
            tfdv_stats_options (dict): Options for generating statistics.
                Can pass pre-defined schema, sampling rate, histogram buckets,
                allowlist for features etc as part of these options. See reference here:
                https://www.tensorflow.org/tfx/data_validation/api_docs/python/tfdv/StatsOptions
        Returns:
            None
    """
    import inspect
    import logging
    import os
    import tensorflow_data_validation as tfdv
    from apache_beam.options.pipeline_options import (
        PipelineOptions,
        GoogleCloudOptions,
        StandardOptions,
        SetupOptions,
        WorkerOptions,
        DebugOptions,
    )

    logging.getLogger().setLevel(logging.INFO)

    def write_setup_py_file():
        """Writes the required setup.py file to disk, ready for use by TFDV"""

        setup_file_contents = inspect.cleandoc(
            f"""
                import setuptools
                setuptools.setup(
                    install_requires=['tensorflow-data-validation=={tfdv.__version__}'],
                    packages=setuptools.find_packages()
                )
        """
        )

        # Create the setup.py file for managing pipeline dependencies
        logging.info("Writing setup.py to disk")
        with open("./setup.py", "w") as f:
            f.write(setup_file_contents)

    pipeline_options = PipelineOptions()
    debug_options = pipeline_options.view_as(DebugOptions)
    google_cloud_options = pipeline_options.view_as(GoogleCloudOptions)
    setup_options = pipeline_options.view_as(SetupOptions)
    standard_options = pipeline_options.view_as(StandardOptions)
    worker_options = pipeline_options.view_as(WorkerOptions)

    if use_dataflow:

        # Set beam_runner to use Dataflow
        logging.info(f"Using Beam Runner: DataflowRunner")
        standard_options.runner = "DataflowRunner"

        # Set Google Cloud options
        if not project_id:
            raise ValueError("You must provide project_id in order to use DataFlow")
        logging.info(f"GCP Project ID: {project_id}")
        google_cloud_options.project = project_id

        if not region:
            raise ValueError("You must provide region in order to use DataFlow")
        logging.info(f"GCP Region: {region}")
        google_cloud_options.region = region

        if not gcs_staging_location:
            raise ValueError(
                "You must provide gcs_staging_location in order to use DataFlow"
            )
        logging.info(f"GCS staging location: {gcs_staging_location}")
        google_cloud_options.staging_location = gcs_staging_location

        if not gcs_temp_location:
            raise ValueError(
                "You must provide gcs_temp_location in order to use DataFlow"
            )
        logging.info(f"GCS temp location: {gcs_temp_location}")
        google_cloud_options.temp_location = gcs_temp_location

        # Set Worker options
        use_public_ips = bool(use_public_ips)  # cast to bool to be sure
        logging.info(f"Dataflow using public IP addresses: {use_public_ips}")
        worker_options.use_public_ips = use_public_ips
        if subnetwork:
            logging.info(f"Dataflow subnetwork: {subnetwork}")
            worker_options.subnetwork = subnetwork

        # If using a prebaked TFDV+Beam container image, set these options
        if tfdv_container_image:
            logging.info(f"Custom Dataflow container: {tfdv_container_image}")
            logging.info("Using Dataflow v2 runner")
            debug_options.add_experiment("use_runner_v2")
            setup_options.sdk_location = "container"
            worker_options.sdk_container_image = tfdv_container_image
        # If not using a prebaked container image, use setup.py for TFDV installation
        else:
            logging.info(f"Using setup.py file. TFDV version is {tfdv.__version__}")
            write_setup_py_file()
            setup_options.setup_file = "./setup.py"

    else:
        # If not using Dataflow, use DirectRunner
        logging.info(f"Using Beam Runner: DirectRunner")
        standard_options.runner = "DirectRunner"

    # Apply any extra pipeline options provided by the user

    for key, val in extra_standard_options.items():
        setattr(standard_options, key, val)

    for key, val in extra_setup_options.items():
        setattr(setup_options, key, val)

    for key, val in extra_google_cloud_options.items():
        setattr(google_cloud_options, key, val)

    for key, val in extra_worker_options.items():
        setattr(worker_options, key, val)

    for key, val in extra_debug_options.items():
        setattr(debug_options, key, val)

    # if file_pattern is provided, join dataset.uri with file_pattern
    dataset_uri = dataset.uri
    if file_pattern:
        dataset_uri = os.path.join(dataset.uri, file_pattern)

    # if stats options are provided, pass those to generate_statistics_from_csv
    stats_options = tfdv.StatsOptions()
    if tfdv_stats_options:
        # if schema is provided, load and pass to stats_options dict
        if "schema" in tfdv_stats_options:
            tfdv_stats_options["schema"] = tfdv.load_schema_text(
                tfdv_stats_options["schema"]
            )
        stats_options = tfdv.StatsOptions(**tfdv_stats_options)

    logging.info(f"Generating statistics from: {dataset_uri}")
    logging.info(f"Saving statistics to: {statistics.uri}")

    tfdv.generate_statistics_from_csv(
        data_location=dataset_uri,
        output_path=statistics.uri,
        pipeline_options=pipeline_options,
        stats_options=stats_options,
    )
