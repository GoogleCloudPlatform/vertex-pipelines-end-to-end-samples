# Single, Mirror and Multi-Machine Distributed Training for CIFAR-10
import json

import tensorflow_datasets as tfds
import tensorflow as tf
from tensorflow.python.client import device_lib
import argparse
import os
import sys

tfds.disable_progress_bar()

parser = argparse.ArgumentParser()
parser.add_argument("--lr", dest="lr", default=0.01, type=float, help="Learning rate.")
parser.add_argument(
    "--epochs", dest="epochs", default=10, type=int, help="Number of epochs."
)
parser.add_argument(
    "--steps", dest="steps", default=200, type=int, help="Number of steps per epoch."
)
parser.add_argument(
    "--distribute",
    dest="distribute",
    type=str,
    default="single",
    help="distributed training strategy",
)
parser.add_argument("--metrics", dest="metrics", type=str)
args = parser.parse_args()

print("Python Version = {}".format(sys.version))
print("TensorFlow Version = {}".format(tf.__version__))
print("TF_CONFIG = {}".format(os.environ.get("TF_CONFIG", "Not found")))
print("DEVICES", device_lib.list_local_devices())

# Single Machine, single compute device
if args.distribute == "single":
    if tf.test.is_gpu_available():
        strategy = tf.distribute.OneDeviceStrategy(device="/gpu:0")
    else:
        strategy = tf.distribute.OneDeviceStrategy(device="/cpu:0")
# Single Machine, multiple compute device
elif args.distribute == "mirror":
    strategy = tf.distribute.MirroredStrategy()
# Multiple Machine, multiple compute device
elif args.distribute == "multi":
    strategy = tf.distribute.experimental.MultiWorkerMirroredStrategy()

# Multi-worker configuration
print("num_replicas_in_sync = {}".format(strategy.num_replicas_in_sync))

# Preparing dataset
BUFFER_SIZE = 10000
BATCH_SIZE = 64


def make_datasets_unbatched():
    # Scaling CIFAR10 data from (0, 255] to (0., 1.]
    def scale(image, label):
        image = tf.cast(image, tf.float32)
        image /= 255.0
        return image, label

    datasets, info = tfds.load(name="cifar10", with_info=True, as_supervised=True)
    return datasets["train"].map(scale).cache().shuffle(BUFFER_SIZE).repeat()


# Build the Keras model
def build_and_compile_cnn_model():
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Conv2D(32, 3, activation="relu", input_shape=(32, 32, 3)),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Conv2D(32, 3, activation="relu"),
            tf.keras.layers.MaxPooling2D(),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(10, activation="softmax"),
        ]
    )
    model.compile(
        loss=tf.keras.losses.sparse_categorical_crossentropy,
        optimizer=tf.keras.optimizers.SGD(learning_rate=args.lr),
        metrics=["accuracy"],
    )
    return model


# Train the model
NUM_WORKERS = strategy.num_replicas_in_sync
# Here the batch size scales up by number of workers since
# `tf.data.Dataset.batch` expects the global batch size.
GLOBAL_BATCH_SIZE = BATCH_SIZE * NUM_WORKERS
MODEL_DIR = os.getenv("AIP_MODEL_DIR")

train_dataset = make_datasets_unbatched().batch(GLOBAL_BATCH_SIZE)

with strategy.scope():
    # Creation of dataset, and model building/compiling need to be within
    # `strategy.scope()`.
    model = build_and_compile_cnn_model()

model.fit(x=train_dataset, epochs=args.epochs, steps_per_epoch=args.steps)
model.save(MODEL_DIR)

metrics = {
    "problemType": "regression",
    "rootMeanSquaredError": 0.01,
    "meanAbsoluteError": 0.02,
    "meanAbsolutePercentageError": 0.03,
    "rSquared": 0.04,
    "rootMeanSquaredLogError": 0.05,
}

with open(args.metrics, "w") as fp:
    json.dump(metrics, fp)
