project_id = "my-test-project"

pubsub_topic_name = "vertex-pipelines-trigger"

cloud_schedulers_config = {
  training = {
    name        = "training-pipeline-trigger",
    region      = "europe-west4", # Must be the same as the App Engine region
    description = "Trigger my training pipeline in Vertex",
    schedule    = "0 0 * * 0",
    time_zone   = "UTC",
    # Relative path to payload JSON file for this environment
    payload_file = "../../pipelines/xgboost/training/payloads/test.json",
  },
}
