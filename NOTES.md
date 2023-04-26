# Sandbox

Steps for manual deployment

1. Perform instructions in "Local setup" section of README.md

2. Update `env.sh` and then source it with `source env.sh`
   
```bash
-- env.sh
export PIPELINE_TEMPLATE=tensorflow
export VERTEX_CMEK_IDENTIFIER= # optional
export VERTEX_LOCATION=northamerica-northeast1
export VERTEX_NETWORK= # optional
export VERTEX_PROJECT_ID=big-data-sandbox-272117
```

3. Create bucket for terraform state

```bash
gsutil mb -l ${VERTEX_LOCATION} -p ${VERTEX_PROJECT_ID} --pap=enforced gs://${VERTEX_PROJECT_ID}-tfstate && gsutil ubla set on gs://${VERTEX_PROJECT_ID}-tfstate
```

4. Create bigquery datasets

```bash
bq --location=${VERTEX_LOCATION} mk --dataset "${VERTEX_PROJECT_ID}:chicago_taxi_trips"
bq --location=${VERTEX_LOCATION} mk --dataset "${VERTEX_PROJECT_ID}:preprocessing"
bq mk --transfer_config \
  --project_id=${VERTEX_PROJECT_ID} \
  --data_source="cross_region_copy" \
  --target_dataset="chicago_taxi_trips" \
  --display_name="Chicago taxi trip mirror" \
  --params='{"source_dataset_id":"'"chicago_taxi_trips"'","source_project_id":"'"bigquery-public-data"'"}'
```

5. Deploy the infra with `make deploy-infra`

The `terraform apply` command was not able to read created by the `terraform init` command, so I had to give the "Storage Object Admin" permission to the owners of the project. The project owners already had the "Storage Legacy Bucket Owner" permission, but it was not enough to read/update the state files.

6. Compile the components with `make compile-all-components`

7. Train the model with `make run pipeline=training`

This command deploys the pipeline to Vertex AI and starts a training job.

Problems found:

- The "Visualize data statistics" step in the training pipeline was failing, so I had to change the dependency from "tensorflow-data-valiation==1.6.0" to "tensorflow-data-validation[visualization]==1.6.0"
- The "Show anomalies" step in the training pipeline was founding one anomaly and failing. This error would stop the execution of the remaining steps in the pipeline, so I changed the "fail_on_anomalies" parameter to "False".
- Also disabled the "fail_on_anomalies" parameter in the prediction pipeline in order to run the pipeline to completion
  
