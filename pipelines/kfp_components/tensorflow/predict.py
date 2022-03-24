from kfp.v2.dsl import Dataset, Input, Output, Model, component
from pipelines.kfp_components.dependencies import PYTHON37, TENSORFLOW, PANDAS


@component(base_image=PYTHON37, packages_to_install=[TENSORFLOW, PANDAS])
def predict_tensorflow_model(
    input_data: Input[Dataset],
    model: Input[Model],
    predictions: Output[Dataset],
    label_column_name: str = None,
    predictions_column_name: str = "predictions",
    file_pattern: str = None,
) -> None:
    """Make predictions using a trained Tensorflow Keras model.

    Args:
        input_data (Input[Dataset]): Input data as kfp's Dataset object.
            Attribute .path is the GCS location for a single csv file.
        model (Input[Model]): Trained model as a kfp Model object.
            Attribute .path is the GCS location for all model files
            (including the main protobuf file)
        predictions (Output[Dataset]): Output data with predictions as kfp's
            Dataset object.
            Attribute .path is the GCS location for a single csv file.
        label_column_name (str): Name of column containing the labels. Defaults to None
        predictions_column_name (str): Name of column in which to save the predicted
            labels. Defaults to "predictions".
        file_pattern (str): Read data from one or more files. If empty,
            then prediction data is read from single file.
            For multiple files, use a pattern e.g. "files-*.csv".

    Returns:
        None
    """
    import logging
    import tensorflow as tf
    import pandas
    from typing import Iterator
    from pathlib import Path

    logging.getLogger().setLevel(logging.INFO)

    def read_files(
        path: Path, file_pattern: str = None, **kwargs
    ) -> Iterator[pandas.DataFrame]:
        """
            Read from one or multiple files using `pandas.read_csv`. Provide a
            file pattern to read from multiple files e.g. "files-*.csv".
        Args:
            path (Path): Path of single file or folder containing multiple files.
            file_pattern (str): If path points to single file, don't provide a pattern.
                Otherwise e.g. "files-*.csv".
            **kwargs: Additional keyword-arguments for `pandas.read_csv`.

        Returns:
            Iterator[pandas.DataFrame]: Iterator of Pandas DataFrames.
        """
        paths = [path]
        if file_pattern:
            logging.info(f"Searching files with pattern {file_pattern} in {path}")
            paths = list(path.glob(file_pattern))
            logging.info(f"Found {len(paths)} files")
            if len(paths) == 0:
                raise RuntimeError("No input files found!")

        for p in paths:
            logging.info(f"Reading file: {p}")
            yield pandas.read_csv(p, **kwargs)

        logging.info("Finished reading files")

    def create_dataset(input_data: Path, file_pattern: str = "") -> tf.data.Dataset:
        """Create a TF Dataset from input csv files

        Args:
            input_data (Path): Train/Valid data in CSV format
            file_pattern (str): Read data from one or more files. If empty, then
                prediction data is read from single file.
                For multiple files, use a pattern e.g. "files-*.csv".
        Returns:
            dataset: TF dataset where each element is a (features, labels)
                tuple that corresponds to a batch of CSV rows
        """
        if file_pattern:
            input_data = input_data / file_pattern

        # Apply data sharding: Sharded elements are produced by the dataset
        # Each worker will process the whole dataset and discard the portion that is
        # not for itself. Note that for this mode to correctly partitions the dataset
        # elements, the dataset needs to produce elements in a deterministic order.
        data_options = tf.data.Options()
        data_options.experimental_distribute.auto_shard_policy = (
            tf.data.experimental.AutoShardPolicy.DATA
        )

        created_dataset = tf.data.experimental.make_csv_dataset(
            file_pattern=str(input_data),
            batch_size=100,
            label_name=label_column_name,
            num_epochs=1,
            shuffle=False,
            num_parallel_reads=1,
        )
        return created_dataset.with_options(data_options)

    logging.info(f"Read data from {input_data.path}")
    df = pandas.concat(read_files(Path(input_data.path), file_pattern))

    logging.info("Create TF Dataset for prediction input")
    pred_input = create_dataset(Path(input_data.path), file_pattern)

    logging.info(f"Load model from {model.path}")
    tf_model = tf.keras.models.load_model(model.path)

    logging.info("Predict...")
    df[predictions_column_name] = tf_model.predict(pred_input)

    logging.info(f"Save predictions to {predictions.path}")
    df.to_csv(predictions.path, sep=",", header=True, index=False)
