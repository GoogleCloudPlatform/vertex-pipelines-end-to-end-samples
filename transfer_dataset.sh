#!/bin/bash
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


SRC_PROJECT_ID='bigquery-public-data'
SRC_DATASET='chicago_taxi_trips'
DES_PROJECT_ID=${1}
DES_DATASET=${2:-'chicago_taxi_trips'}
DES_LOCATION=${3:-'EU'}
JOB_NAME='Copy public dataset across regions'

echo "Creating dataset $DES_DATASET ($DES_PROJECT_ID) in $DES_LOCATION..."
bq --location="$DES_LOCATION" mk --dataset "$DES_PROJECT_ID:$DES_DATASET"

echo "Requesting transfer of dataset $SRC_DATASET ($SRC_PROJECT_ID) to $DES_DATASET ($DES_PROJECT_ID)..."
bq mk --transfer_config \
  --project_id="$DES_PROJECT_ID" \
  --data_source="cross_region_copy" \
  --target_dataset="$DES_DATASET" \
  --display_name="$JOB_NAME" \
  --params='{"source_dataset_id":"'"$SRC_DATASET"'","source_project_id":"'"$SRC_PROJECT_ID"'"}'

echo "Transfer requested! Monitor progress in cloud console at https://console.cloud.google.com/bigquery/transfers"
