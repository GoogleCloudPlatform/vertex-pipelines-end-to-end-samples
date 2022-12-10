# Copyright 2022 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

project_id = "my-prod-project"

pubsub_topic_name = "vertex-pipelines-trigger"

cloud_schedulers_config = {
  # Uncomment and amend as required

  # xgboost_training = {
  #   name         = "xgboost-training-pipeline-trigger"
  #   region       = "europe-west4"
  #   description  = "Trigger my XGBoost training pipeline in Vertex"
  #   schedule     = "0 0 * * 0"
  #   time_zone    = "UTC"
  #   template_path = "gs://my-compiled-pipelines-bucket/<Git tag>/training.json"
  #   enable_caching = null
  #   pipeline_parameters = {
  #     project_id = "my-prod-project"
  #     project_location = "europe-west4"
  #     pipeline_files_gcs_path = "gs://my-assets-bucket/assets/<Git tag>/training/files"
  #     ingestion_project_id = "my-prod-project"
  #     model_name = "xgboost-with-preprocessing"
  #     model_label = "label_name"
  #     tfdv_schema_filename = "tfdv_schema_training.pbtxt"
  #     tfdv_train_stats_path = "gs://my-assets-bucket/train_stats/train.stats"
  #     dataset_id = "preprocessing"
  #     dataset_location = "EU"
  #     ingestion_dataset_id = "chicago_taxi_trips"
  #     timestamp = "2021-08-01 00:00:00"
  #   },
  # },

  # xgboost_prediction = {
  #   name         = "xgboost-prediction-pipeline-trigger"
  #   region       = "europe-west4"
  #   description  = "Trigger my XGBoost prediction pipeline in Vertex"
  #   schedule     = "0 0 * * 0"
  #   time_zone    = "UTC"
  #   template_path = "gs://my-compiled-pipelines-bucket/<Git tag>/prediction.json"
  #   enable_caching = null
  #   pipeline_parameters = {
  #     project_id = "my-prod-project"
  #     project_location = "europe-west4"
  #     pipeline_files_gcs_path = "gs://my-assets-bucket/assets/<Git tag>/prediction/files"
  #     ingestion_project_id = "my-prod-project"
  #     model_name = "xgboost-with-preprocessing"
  #     model_label = "label_name"
  #     tfdv_schema_filename = "tfdv_schema_training.pbtxt"
  #     tfdv_train_stats_path = "gs://my-assets-bucket/train_stats/train.stats"
  #     dataset_id = "preprocessing"
  #     dataset_location = "EU"
  #     ingestion_dataset_id = "chicago_taxi_trips"
  #     timestamp = "2021-08-01 00:00:00"
  #     batch_prediction_machine_type = "n1-standard-4"
  #     batch_prediction_min_replicas = 3
  #     batch_prediction_max_replicas = 5
  #   },
  # },

  # tensorflow_training = {
  #   name         = "tensorflow-training-pipeline-trigger"
  #   region       = "europe-west4"
  #   description  = "Trigger my TensorFlow training pipeline in Vertex"
  #   schedule     = "0 0 * * 0"
  #   time_zone    = "UTC"
  #   template_path = "gs://my-compiled-pipelines-bucket/<Git tag>/training.json"
  #   enable_caching = null
  #   pipeline_parameters = {
  #     project_id = "my-prod-project"
  #     project_location = "europe-west4"
  #     pipeline_files_gcs_path = "gs://my-assets-bucket/assets/<Git tag>/training/files"
  #     ingestion_project_id = "my-prod-project"
  #     model_name = "tensorflow-with-preprocessing"
  #     model_label = "label_name"
  #     tfdv_schema_filename = "tfdv_schema_training.pbtxt"
  #     tfdv_train_stats_path = "gs://my-assets-bucket/train_stats/train.stats"
  #     dataset_id = "preprocessing"
  #     dataset_location = "EU"
  #     ingestion_dataset_id = "chicago_taxi_trips"
  #     timestamp = "2021-08-01 00:00:00"
  #   },
  # },

  # tensorflow_prediction = {
  #   name         = "tensorflow-prediction-pipeline-trigger"
  #   region       = "europe-west4"
  #   description  = "Trigger my TensorFlow prediction pipeline in Vertex"
  #   schedule     = "0 0 * * 0"
  #   time_zone    = "UTC"
  #   template_path = "gs://my-compiled-pipelines-bucket/<Git tag>/prediction.json"
  #   enable_caching = null
  #   pipeline_parameters = {
  #     project_id = "my-prod-project"
  #     project_location = "europe-west4"
  #     pipeline_files_gcs_path = "gs://my-assets-bucket/assets/<Git tag>/prediction/files"
  #     ingestion_project_id = "my-prod-project"
  #     model_name = "tensorflow-with-preprocessing"
  #     model_label = "label_name"
  #     tfdv_schema_filename = "tfdv_schema_training.pbtxt"
  #     tfdv_train_stats_path = "gs://my-assets-bucket/train_stats/train.stats"
  #     dataset_id = "preprocessing"
  #     dataset_location = "EU"
  #     ingestion_dataset_id = "chicago_taxi_trips"
  #     timestamp = "2021-08-01 00:00:00"
  #     batch_prediction_machine_type = "n1-standard-4"
  #     batch_prediction_min_replicas = 3
  #     batch_prediction_max_replicas = 5
  #   },
  # },
}
