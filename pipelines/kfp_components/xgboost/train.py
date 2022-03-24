from kfp.v2.dsl import Artifact, Input, Output, Dataset, Model, component
from pipelines.kfp_components.dependencies import PYTHON37, XGBOOST, SKLEARN, PANDAS


@component(
    base_image=PYTHON37,
    packages_to_install=[XGBOOST, SKLEARN, PANDAS],
)
def train_xgboost_model(
    training_data: Input[Dataset],
    validation_data: Input[Dataset],
    file_pattern: str,
    label_name: str,
    model_params: dict,
    model: Output[Model],
    metrics_artifact: Output[Artifact],
) -> None:
    """Train an XGBoost model.

    Args:
        training_data (Input[Dataset]): Training data as kfp's Dataset object.
            Attribute .path is the GCS location for csv files
        validation_data (Input[Dataset]): Validation data as kfp's Dataset object.
            Attribute .path is the GCS location for csv files
        file_pattern (str): Read data from one or more files. If empty,
            then training and validation data is read from single file
            respectively. For multiple files, use a pattern e.g. "files-*.csv".
        label_name (str): CSV column name containing the label data.
        model_params (dict): Dictionary of following training parameters
            num_iterations: int - Number of boosting iterations.
            booster_params: int/str/float - Parameters for the booster.
                See https://xgboost.readthedocs.io/en/latest/parameter.html
            early_stopping_rounds: int - Early stopping rounds (optional).
        model (Output[Model]): Output model as a kfp Model object.
            Attribute .path is the GCS location for the trained model
            in SKLearn joblib format
        metrics_artifact (Output[Artifact]): Output metrics of all iterations for
            the trained model in JSON format.

    Returns:
        None
    """
    import json
    import os
    import logging
    import pandas
    import joblib
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler, OrdinalEncoder, OneHotEncoder
    from sklearn.compose import ColumnTransformer
    from xgboost import XGBRegressor
    from typing import Iterator
    from pathlib import Path

    # numeric/categorical features in Chicago trips dataset to be preprocessed
    NUM_COLS = ["dayofweek", "hourofday", "trip_distance", "trip_miles", "trip_seconds"]
    ORD_COLS = ["company"]
    OHE_COLS = ["payment_type"]

    logging.getLogger().setLevel(logging.INFO)

    def read_files(
        path: Path, file_pattern: str = None, **kwargs
    ) -> Iterator[pandas.DataFrame]:
        """
            Read from one or multiple files using `pandas.read_csv`. Provide a
            file pattern to read from multiple files e.g. "files-*.csv".
        Args:
            path: Path of single file or folder containing multiple files.
            file_pattern: If path points to single file, don't provide a pattern.
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

    def indices_in_list(elements: list, base_list: list) -> list:
        """Get indices of specific elements in a base list

        Args:
            elements (list): Specific elements to fetch indices for
            base_list (list): Overall list containing all possible elements
        Returns:
            list: List of indices for the specific elements
        """
        return [idx for idx, elem in enumerate(base_list) if elem in elements]

    logging.info("Read train & validation data into pandas dataframes")
    train_df = pandas.concat(read_files(Path(training_data.path), file_pattern))
    valid_df = pandas.concat(read_files(Path(validation_data.path), file_pattern))

    logging.info("Split train/validation data into features & labels")
    X_train, y_train = (
        train_df.drop(columns=[label_name]),
        train_df[label_name],
    )
    X_valid, y_valid = (
        valid_df.drop(columns=[label_name]),
        valid_df[label_name],
    )

    logging.info("Get the number of unique categories for ordinal encoded columns")
    ordinal_columns = X_train[ORD_COLS]
    n_unique_cat = ordinal_columns.nunique()

    logging.info("Get indices of columns in base data")
    col_list = X_train.columns.tolist()
    num_indices = indices_in_list(NUM_COLS, col_list)
    cat_indices_onehot = indices_in_list(OHE_COLS, col_list)
    cat_indices_ordinal = indices_in_list(ORD_COLS, col_list)

    logging.info(
        "Create transformers for each ordinal column based on the ORD_COLS variable"
    )
    ordinal_transformers = [
        (
            f"ordinal encoding for {ord_col}",
            OrdinalEncoder(
                handle_unknown="use_encoded_value", unknown_value=n_unique_cat[ord_col]
            ),
            [ord_index],
        )
        for ord_col in ORD_COLS
        for ord_index in cat_indices_ordinal
    ]
    all_transformers = [
        ("numeric_scaling", StandardScaler(), num_indices),
        (
            "one_hot_encoding",
            OneHotEncoder(handle_unknown="ignore"),
            cat_indices_onehot,
        ),
    ] + ordinal_transformers

    logging.info("Build sklearn preprocessing steps")
    preprocesser = ColumnTransformer(transformers=all_transformers)

    logging.info("Transform validation data - Required for evaluation")
    valid_preprocesser = preprocesser.fit(X_train)
    X_valid_transformed = valid_preprocesser.transform(X_valid)

    logging.info("Build sklearn pipeline with XGBoost model")
    xgb_model = XGBRegressor(**model_params)

    pipeline = Pipeline(
        steps=[("feature_engineering", preprocesser), ("train_model", xgb_model)]
    )

    # eval_set is an input argument for XGBRegressor. Need to pass this argument
    # to the Pipeline in the following format {step_name}__{argument_name}
    pipeline.fit(
        X_train, y_train, train_model__eval_set=[(X_valid_transformed, y_valid)]
    )

    logging.info("Save evaluation results to a dictionary")
    # Fetch evals_result from 'train_model' step of the Pipeline object
    evals_result = pipeline.named_steps["train_model"].evals_result()

    # ensure to change GCS to local mount path
    os.makedirs(model.path, exist_ok=True)

    logging.info(f"Save model to: {model.path}")
    joblib.dump(pipeline, model.path + "/model.joblib")

    logging.info(f"Save metrics to: {metrics_artifact.path}")
    with open(metrics_artifact.path, "w") as fp:
        json.dump(evals_result, fp)
