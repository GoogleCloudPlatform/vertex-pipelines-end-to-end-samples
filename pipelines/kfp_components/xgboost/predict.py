from kfp.v2.dsl import Dataset, Input, Output, Model, component
from pipelines.kfp_components.dependencies import PYTHON37, XGBOOST, SKLEARN, PANDAS


@component(base_image=PYTHON37, packages_to_install=[XGBOOST, SKLEARN, PANDAS])
def predict_xgboost_model(
    input_data: Input[Dataset],
    model: Input[Model],
    predictions: Output[Dataset],
    label_column_name: str = None,
    predictions_column_name: str = "predictions",
    file_pattern: str = None,
) -> None:
    """Make predictions using a trained XGBoost model.

    Args:
        input_data (Input[Dataset]): Input data as kfp's Dataset object.
            Attribute .path is the GCS location for a single csv file.
        model (Input[Model]): Trained model as a kfp Model object.
            Attribute .path is the GCS location for the model in binary XGBoost
            format.
        predictions (Output[Dataset]): Output data with predictions as kfp's Dataset
            object.
            Attribute .path is the GCS location for a single csv file.
        label_column_name (str): Name of column containing the labels.
            Defaults to None.
        predictions_column_name (str): Name of column in which to save the predicted
            labels. Defaults to "predictions".
        file_pattern (str): Read data from one or more files. If empty,
            then prediction data is read from single file.
            For multiple files, use a pattern e.g. "files-*.csv".
    Returns:
        None
    """
    import logging
    import os
    import pandas
    import joblib
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

    # read input data
    df = pandas.concat(read_files(Path(input_data.path), file_pattern))

    # exclude label column if provided
    X = df.drop(columns=[label_column_name]) if label_column_name else df

    # load model
    model_path = os.path.join(model.path, "model.joblib")
    model = joblib.load(model_path)

    # predict and save to prediction column
    df[predictions_column_name] = model.predict(X)

    # save dataframe (feature, labels if provided, predictions)
    df.to_csv(predictions.path, sep=",", header=True, index=False)
