#!/bin/bash 
export PAYLOAD=dev.json
export PIPELINE_FILES_GCS_PATH=gs://datatonic-vertex-pipeline-dev-pipelines/pipelines
# pipeline template - update to any pipelines under the pipelines folder
# tensorflow or xgboost
export PIPELINE_TEMPLATE=demo
export VERTEX_CMEK_IDENTIFIER= # optional
export VERTEX_LOCATION=europe-west4
export VERTEX_NETWORK= # optional
export VERTEX_PIPELINE_ROOT=gs://datatonic-vertex-pipeline-dev-pipelines/pipeline_root
export VERTEX_PROJECT_ID=datatonic-vertex-pipeline-dev
export VERTEX_SA_EMAIL=vertex-pipeline-runner@datatonic-vertex-pipeline-dev.iam.gserviceaccount.com
