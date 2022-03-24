from kfp.v2.dsl import Artifact, Input, Output, Dataset, Model, component
from pipelines.kfp_components.dependencies import PYTHON37, TENSORFLOW


@component(base_image=PYTHON37, packages_to_install=[TENSORFLOW])
def train_tensorflow_model(
    training_data: Input[Dataset],
    validation_data: Input[Dataset],
    file_pattern: str,
    label_name: str,
    model_params: dict,
    model: Output[Model],
    metrics_artifact: Output[Artifact],
):
    """Train a Tensorflow Keras model.

    Args:
        training_data (Input[Dataset]): Training data as kfp's Dataset object.
            Attribute .path is the GCS location for csv files
        validation_data (Input[Dataset]): Validation data as kfp's Dataset object.
            Attribute .path is the GCS location for csv files
        label_name (str): Name of column containing the labels.
        file_pattern (str): Read data from one or more files. If empty, then
            training and validation data is read from single file respectively.
            For multiple files, use a pattern e.g. "files-*.csv".
        model_params (dict): Dictionary of following training parameters
            batch_size: int (defaults to 100)
            epochs: int (defaults to 5)
            learning rate: float (defaults to 0.001)
            hidden_units: list(tuple) (defaults to [(10, 'relu')])
                Example - [(64, "relu"), (32, "elu")]
                creates 1st dense layer with 64 nodes & activation function as relu
                & 2nd dense layer with 32 nodes & activation function as elu
                Reference (activation functions):
                    https://www.tensorflow.org/api_docs/python/tf/keras/activations
            loss_fn: str (defaults to MeanSquaredError)
                Regression:
                    MeanSquaredError, MeanAbsoluteError, MeanAbsolutePercentageError
                Classification:
                    BinaryCrossentropy,
                    CategoricalCrossentropy, SparseCategoricalCrossentropy
                Reference:
                    https://www.tensorflow.org/api_docs/python/tf/keras/losses
            optimizer: str (defaults to Adam)
                Supported values:
                    Adam, Adadelta, Adamax, Adagrad,
                    Ftrl, RMSprop, SGD
                Reference:
                    https://www.tensorflow.org/api_docs/python/tf/keras/optimizers
            metrics: list (defaults to ['Accuracy'])
                Reference:
                    https://www.tensorflow.org/api_docs/python/tf/keras/metrics
            distribute strategy: str (defaults to single)
                Supported values:
                    Without GPU: single
                    With GPU: single, mirror, multi
            early_stopping_epochs: int (defaults to 5)
                No of epochs to check for training loss convergence
        model (Output[Model]): Output model as a kfp Model object.
            Attribute .path is the GCS location for the trained model
            binaries in protobuf format
        metrics_artifact (Output[Artifact]): Output metrics of all iterations for
            the trained model in JSON format.
    """
    import os
    import json
    import logging
    import tensorflow as tf
    from pathlib import Path
    from tensorflow.data import Dataset
    from tensorflow.keras import Input, Model, optimizers
    from tensorflow.keras.layers import Dense, Normalization, StringLookup, Concatenate

    # numeric/categorical features in Chicago trips dataset to be preprocessed
    NUM_COLS = ["dayofweek", "hourofday", "trip_distance", "trip_miles", "trip_seconds"]
    ORD_COLS = ["company"]
    OHE_COLS = ["payment_type"]

    logging.getLogger().setLevel(logging.INFO)

    def create_dataset(
        input_data: Path, label_name: str, model_params: dict, file_pattern: str = ""
    ) -> Dataset:
        """Create a TF Dataset from input csv files.

        Args:
            input_data (Input[Dataset]): Train/Valid data in CSV format
            label_name (str): Name of column containing the labels
            model_params (dict): model parameters
            file_pattern (str): Read data from one or more files. If empty, then
                training and validation data is read from single file respectively.
                For multiple files, use a pattern e.g. "files-*.csv".
        Returns:
            dataset (TF Dataset): TF dataset where each element is a (features, labels)
                tuple that corresponds to a batch of CSV rows
        """

        # shuffle & shuffle_buffer_size added to rearrange input data
        # passed into model training
        # num_rows_for_inference is for auto detection of datatypes
        # while creating the dataset.
        # If a float column has a high proportion of integer values (0/1 etc),
        # the method wrongly detects it as a tf.int32 which fails during training time,
        # hence the high hardcoded value (default is 100)

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

        logging.info(f"Creating dataset from CSV file(s) at {input_data}...")
        created_dataset = tf.data.experimental.make_csv_dataset(
            file_pattern=str(input_data),
            batch_size=model_params["batch_size"],
            label_name=label_name,
            num_epochs=model_params["epochs"],
            shuffle=True,
            shuffle_buffer_size=1000,
            num_rows_for_inference=20000,
        )
        return created_dataset.with_options(data_options)

    def get_distribution_strategy(distribute_strategy: str) -> tf.distribute.Strategy:
        """Set distribute strategy based on input string.

        Args:
            distribute_strategy (str): single, mirror or multi
        Returns:
            strategy (tf.distribute.Strategy): distribution strategy
        """
        logging.info(f"Distribution strategy: {distribute_strategy}")

        # Single machine, single compute device
        if distribute_strategy == "single":
            if len(tf.config.list_physical_devices("GPU")):
                strategy = tf.distribute.OneDeviceStrategy(device="/gpu:0")
            else:
                strategy = tf.distribute.OneDeviceStrategy(device="/cpu:0")
        # Single machine, multiple compute device
        elif distribute_strategy == "mirror":
            strategy = tf.distribute.MirroredStrategy()
        # Multiple machine, multiple compute device
        elif distribute_strategy == "multi":
            strategy = tf.distribute.MultiWorkerMirroredStrategy()
        else:
            raise RuntimeError(
                f"Distribute strategy: {distribute_strategy} not supported"
            )
        return strategy

    def normalization(name: str, dataset: Dataset) -> Normalization:
        """Create a Normalization layer for a feature.

        Args:
            name (str): name of feature to be normalized
            dataset (Dataset): dataset to adapt layer

        Returns:
            normalization layer (Normalization): adapted normalization layer
                of shape (?,1)
        """
        logging.info(f"Normalizing numerical input '{name}'...")
        x = Normalization(axis=None, name=f"normalize_{name}")
        x.adapt(dataset.map(lambda y, _: y[name]))
        return x

    def str_lookup(name: str, dataset: Dataset, output_mode: str) -> StringLookup:
        """Create a StringLookup layer for a feature.

        Args:
            name (str): name of feature to be encoded
            dataset (Dataset): dataset to adapt layer
            output_mode (str): argument for StringLookup layer (e.g. 'one_hot', 'int')

        Returns:
            StringLookup layer (StringLookup): adapted StringLookup layer of shape (?,X)
        """
        logging.info(f"Encoding categorical input '{name}' ({output_mode})...")
        x = StringLookup(
            output_mode=output_mode, name=f"str_lookup_{output_mode}_{name}"
        )
        x.adapt(dataset.map(lambda y, _: y[name]))
        logging.info(f"Vocabulary: {x.get_vocabulary()}")
        return x

    def build_and_compile_model(dataset: Dataset, model_params: dict) -> Model:
        """Build and compile model.

        Args:
            dataset (Dataset): training dataset
            model_params (dict): model parameters

        Returns:
            model (Model): built and compiled model
        """

        # create inputs (scalars with shape `()`)
        num_ins = {
            name: Input(shape=(), name=name, dtype=tf.float32) for name in NUM_COLS
        }
        ord_ins = {
            name: Input(shape=(), name=name, dtype=tf.string) for name in ORD_COLS
        }
        cat_ins = {
            name: Input(shape=(), name=name, dtype=tf.string) for name in OHE_COLS
        }

        # join all inputs and expand by 1 dimension. NOTE: this is useful when passing
        # in scalar inputs to a model in Vertex AI batch predictions or endpoints e.g.
        # `{"instances": {"input1": 1.0, "input2": "str"}}` instead of
        # `{"instances": {"input1": [1.0], "input2": ["str"]}`
        all_ins = {**num_ins, **ord_ins, **cat_ins}
        exp_ins = {n: tf.expand_dims(i, axis=-1) for n, i in all_ins.items()}

        # preprocess expanded inputs
        num_encoded = [normalization(n, dataset)(exp_ins[n]) for n in NUM_COLS]
        ord_encoded = [str_lookup(n, dataset, "int")(exp_ins[n]) for n in ORD_COLS]
        ohe_encoded = [str_lookup(n, dataset, "one_hot")(exp_ins[n]) for n in OHE_COLS]

        # ensure ordinal encoded layers is of type float32 (like the other layers)
        ord_encoded = [tf.cast(x, tf.float32) for x in ord_encoded]

        # concat encoded inputs and add dense layers including output layer
        x = num_encoded + ord_encoded + ohe_encoded
        x = Concatenate()(x)
        for units, activation in model_params["hidden_units"]:
            x = Dense(units, activation=activation)(x)
        x = Dense(1, name="output", activation="linear")(x)

        model = Model(inputs=all_ins, outputs=x, name="nn_model")
        model.summary()

        logging.info(f"Use optimizer {model_params['optimizer']}")
        optimizer = optimizers.get(model_params["optimizer"])
        optimizer.learning_rate = model_params["learning_rate"]

        model.compile(
            loss=model_params["loss_fn"],
            optimizer=optimizer,
            metrics=model_params["metrics"],
        )

        return model

    def _is_chief(strategy: tf.distribute.Strategy) -> bool:
        """Determine whether current worker is the chief (master). See more info:
        - https://www.tensorflow.org/tutorials/distribute/multi_worker_with_keras
        - https://www.tensorflow.org/api_docs/python/tf/distribute/cluster_resolver/ClusterResolver # noqa: E501

        Args:
            strategy (tf.distribute.Strategy): strategy

        Returns:
            is_chief (bool): True if worker is chief, otherwise False
        """
        cr = strategy.cluster_resolver
        return (cr is None) or (cr.task_type == "chief" and cr.task_id == 0)

    def save_model_outputs(
        model_path: str,
        metrics_artifact_path: str,
        model: Model,
        strategy: tf.distribute.Strategy,
    ) -> None:
        """Save model outputs only for chief - Model binaries + Metrics

        Args:
            model_path (str): Original model path where chief saves model artifacts
            metrics_artifact_path (str): Path where chief will save eval metrics
            model (tf.keras.Model): Trained TF Keras model
            strategy (tf.distribute.Strategy): strategy

        Returns:
            None
        """
        is_chief = _is_chief(strategy)

        if is_chief:
            # Save model artefacts only from chief
            model.save(model_path, save_format="tf")
            # Save metrics only from chief
            with open(metrics_artifact_path, "w") as fp:
                json.dump(history.history, fp)

    # prepare model params
    default_model_params = dict(
        batch_size=100,
        epochs=5,
        loss_fn="MeanSquaredError",
        optimizer="Adam",
        learning_rate=0.001,
        metrics=["Accuracy"],
        hidden_units=[(10, "relu")],
        distribute_strategy="single",
        early_stopping_epochs=5,
    )
    # merge dictionaries by overwriting default_model_params if provided in model_params
    model_params = {**default_model_params, **model_params}
    logging.info(f"Using model hyper-parameters: {model_params}")

    # Set distribute strategy before any TF operations
    strategy = get_distribution_strategy(model_params["distribute_strategy"])

    train_ds = create_dataset(
        Path(training_data.path), label_name, model_params, file_pattern
    )
    valid_ds = create_dataset(
        Path(validation_data.path), label_name, model_params, file_pattern
    )

    train_features = list(train_ds.element_spec[0].keys())
    valid_features = list(valid_ds.element_spec[0].keys())
    logging.info(f"Training feature names: {train_features}")
    logging.info(f"Validation feature names: {valid_features}")

    if len(train_features) != len(valid_features):
        raise RuntimeError(f"No. of training features != # validation features")

    with strategy.scope():
        tf_model = build_and_compile_model(train_ds, model_params)

    logging.info("Use early stopping")
    callback = tf.keras.callbacks.EarlyStopping(
        monitor="loss", mode="min", patience=model_params["early_stopping_epochs"]
    )

    logging.info("Fit model...")
    history = tf_model.fit(
        train_ds,
        batch_size=model_params["batch_size"],
        epochs=model_params["epochs"],
        validation_data=valid_ds,
        callbacks=[callback],
    )

    # only persist output files if current worker is chief
    os.makedirs(model.path, exist_ok=True)
    logging.info(f"Save model to: {model.path}")
    logging.info(f"Save metrics to: {metrics_artifact.path}")
    save_model_outputs(model.path, metrics_artifact.path, tf_model, strategy)
