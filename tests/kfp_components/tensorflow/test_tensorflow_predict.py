from unittest import mock
import pandas as pd
import numpy as np
from kfp.v2.dsl import (
    Dataset,
    Model,
)


def test_predict_tensorflow_model(tmpdir, make_csv_file):
    """
    Test that the outputs of predict_tensorflow_model exist, and that the output
    predictions have the expected size and contain no NaN values.

    Args:
        tmpdir: pytest tmpdir fixture
        make_csv_file: pytest fixture defined in conftest.py

    Returns:
        None
    """

    from pipelines.kfp_components.tensorflow import predict_tensorflow_model

    # Create paths
    test_data_path = tmpdir.join("test_data.csv")
    model_dir = tmpdir.join("tf_model_files/")
    model_path = model_dir.join("model.pb")
    predictions_path = tmpdir.join("predictions.csv")

    # Create test data as a CSV file
    predictions_col = "predictions"
    n_features, n_rows = 5, 100
    make_csv_file(n_features, n_rows, test_data_path)

    # Prepare artifacts
    test_data = Dataset(uri=str(test_data_path))
    model = Model(uri=str(model_path))
    predictions = Dataset(uri=str(predictions_path))

    with mock.patch("tensorflow.keras.models.load_model") as load_model:
        constant_prediction = 0.42
        load_model.return_value.predict.return_value = np.array(
            [constant_prediction] * n_rows
        )

        # Invoke TF prediction
        predict_tensorflow_model(
            test_data,
            model,
            predictions,
            label_column_name="label",
            predictions_column_name=predictions_col,
        )

    # Check outputs
    assert predictions_path.exists()
    df_predictions = pd.read_csv(predictions_path)
    assert df_predictions.shape[0] == n_rows
    assert (
        df_predictions.shape[1] == n_features + 2
    )  # 5 features, 1 label, 1 prediction
    assert predictions_col in df_predictions
    assert (
        df_predictions[predictions_col].isna().sum() == 0
    )  # Check NaN values for the prediction
