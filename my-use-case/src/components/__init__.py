from kfp.v2.dsl import Dataset, Input, Output, Model, component
from src.dependencies import PYTHON37, XGBOOST, SKLEARN, PANDAS

BASE_IMAGE = "gcr.io/my-org/my-image"


@component(base_image=BASE_IMAGE)
def TrainOp(
    training_data: Input[Dataset],
    model: Output[Model],
):
    import my_use_case

    my_use_case.logic.train.train(training_data.path, model.path)
