import numpy as np
import pandas as pd
from kfp.v2.dsl import Artifact, Dataset, Model


NUM_COLS = ["dayofweek", "hourofday", "trip_distance", "trip_miles", "trip_seconds"]
ORD_COLS = ["company"]
OHE_COLS = ["payment_type"]


def test_train_tensorflow_model(tmpdir):
    """Test that the outputs of train_tensorflow_model exist

    Args:
        tmpdir: pytest tmpdir fixture
    Returns:
        None
    """
    from pipelines.kfp_components.tensorflow import train_tensorflow_model

    # Generate random training/validation data
    n_rows = 100
    train_path = tmpdir.join("train.csv")
    train_df = pd.DataFrame(
        np.random.rand(n_rows, len(NUM_COLS) + 1), columns=["label"] + NUM_COLS
    )
    train_df[ORD_COLS], train_df[OHE_COLS] = "test", "test"
    train_df.to_csv(train_path, index=False)

    # Prepare arguments
    file_pattern = ""
    label_column_name = "label"
    tf_params = dict(
        batch_size=16,
        epochs=1,
        loss_fn="MeanSquaredError",
        optimizer="Adam",
        learning_rate=0.3,
        distribute_strategy="single",
        hidden_units=[(2, "relu")],
        metrics="MeanSquaredError",
    )
    training_data = Dataset(uri=train_path)
    validation_data = Dataset(uri=train_path)
    model = Model(uri=str(tmpdir.join("/model")))
    metrics_artifact = Artifact(uri=str(tmpdir.join("metrics.json")))

    # invoke training
    train_tensorflow_model(
        training_data=training_data,
        validation_data=validation_data,
        file_pattern=file_pattern,
        label_name=label_column_name,
        model_params=tf_params,
        model=model,
        metrics_artifact=metrics_artifact,
    )

    # Check outputs
    assert (tmpdir.join("/model") / "saved_model.pb").exists()
    assert (tmpdir.join("/model") / "keras_metadata.pb").exists()
    assert (tmpdir / "metrics.json").exists()
