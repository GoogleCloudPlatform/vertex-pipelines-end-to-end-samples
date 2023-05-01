# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from kfp.v2 import compiler, dsl
from kfp.v2.components import importer_node
from pipelines.components import (
    custom_train_job,
    update_best_model,
    import_model_evaluation,
)


SKL_SERVING_CONTAINER_IMAGE_URI = (
    "europe-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.0-24:latest"
)


@dsl.pipeline(name="xgboost-train-pipeline")
def my_pipeline(
    project_id: str = os.environ.get("VERTEX_PROJECT_ID"),
    project_location: str = os.environ.get("VERTEX_LOCATION"),
):

    test_dataset = importer_node.importer(
        artifact_uri="gs://dt-turbo-templates-dev-pl-root/1006617939274/xgboost-train-pipeline-20230428143046/extract-bq-to-dataset-3_-4883959182325186560/dataset",  # noqa: E501
        artifact_class=dsl.Dataset,
    )
    task = importer_node.importer(
        artifact_uri="gs://dt-turbo-templates-dev-pl-assets/training/assets/task.py",
        artifact_class=dsl.Artifact,
    )

    model_params = dict(
        n_estimators=10,
        early_stopping_rounds=10,
        objective="reg:squarederror",
        booster="gbtree",
        learning_rate=0.3,
        min_split_loss=0,
        max_depth=6,
    )

    train_model = custom_train_job(
        task=task.output,
        project_id=project_id,
        project_location=project_location,
    )

    evaluation = import_model_evaluation(
        model=train_model.outputs["model"],
        metrics=train_model.outputs["metrics"],
        test_dataset=test_dataset.output,
        # TODO use "{{$.pipeline_job_name}}" instead
        pipeline_job_id="xgboost-train-pipeline-20230501121155",
        project_location=project_location,
    )

    with dsl.Condition(train_model.outputs["parent_model"] != "", "champion-exists"):
        update_best_model(
            challenger=train_model.outputs["model"],
            challenger_evaluation=evaluation.outputs["model_evaluation"],
            parent_model=train_model.outputs["parent_model"],
            primary_metric="rootMeanSquaredError",
            project_id=project_id,
            project_location=project_location,
        )


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=my_pipeline,
        package_path="training.json",
        type_check=False,
    )
