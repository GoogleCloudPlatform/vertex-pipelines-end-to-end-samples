from kfp.v2 import compiler, dsl
from my_use_case.components import TrainOp


@dsl.pipeline(name="my-pipeline")
def my_pipeline():
    train_op = TrainOp()


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=my_pipeline,
        package_path="my_pipeline.json",
        type_check=False,
    )
