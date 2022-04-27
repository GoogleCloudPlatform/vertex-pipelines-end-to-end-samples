#!/bin/bash

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
