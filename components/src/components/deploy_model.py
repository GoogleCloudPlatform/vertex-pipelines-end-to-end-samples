# Copyright 2023 Google LLC
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

from typing import NamedTuple

from kfp.dsl import Input, Model, component


@component(
    base_image="python:3.12.8",
    packages_to_install=["google-cloud-aiplatform==1.135.0"],
)
def deploy_model(
    vertex_model: Input[Model],
    project: str,
    location: str,
    endpoint_name: str,
    service_account: str,
    machine_type: str = "n2-highcpu-2",
    traffic_percentage: int = 100,
    min_replica_count: int = 1,
    max_replica_count: int = 1,
    enable_request_response_logging: bool = False,
    logging_sampling_rate: float = 0.3,
    bq_logging_destination_table: str = "",
) -> NamedTuple("Outputs", [("endpoint_id", str), ("logging_bq_table", str)]):
    """
    Deploy a model to a Vertex AI endpoint using a rolling strategy.

    Finds an existing endpoint by display name or creates a new one, then
    deploys the model. If there are already models on the endpoint, the new
    model receives ``traffic_percentage`` and the previous model gets the
    remainder. Models older than the two most recent are undeployed.

    When ``enable_request_response_logging`` is True, a newly created endpoint
    logs sampled predict request/response payloads to BigQuery so Model
    Monitoring v2 can analyse the traffic. Logging can only be set at endpoint
    creation time; an existing endpoint is left unchanged.

    Args:
        vertex_model: VertexModel artifact from the upload_model component.
        project: GCP project ID.
        location: GCP region (e.g. europe-west2).
        endpoint_name: Display name for the endpoint.
        service_account: Service account for the deployed model.
        machine_type: Machine type for serving.
        traffic_percentage: Percentage of traffic for the new deployment.
        min_replica_count: Minimum replica count.
        max_replica_count: Maximum replica count.
        enable_request_response_logging: Enable predict request/response
            logging on a newly created endpoint.
        logging_sampling_rate: Fraction of requests to log (0.0–1.0).
        bq_logging_destination_table: Optional ``bq://project.dataset.table``
            destination. If empty, Vertex AI auto-creates a table.
    """

    import logging
    import re

    import google.cloud.aiplatform as aip

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    def _default_logging_table() -> str:
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", endpoint_name)
        return "bq://" + f"{project}.logging_{safe_name}" + ".request_response_logging"

    def _logging_table_uri(endpoint) -> str:
        gca = getattr(endpoint, "gca_resource", None) or getattr(
            endpoint, "_gca_resource", None
        )
        if gca is None:
            return ""
        cfg = getattr(gca, "predict_request_response_logging_config", None)
        if cfg is None or not getattr(cfg, "enabled", False):
            return ""
        dest = getattr(cfg, "bigquery_destination", None)
        return getattr(dest, "output_uri", "") or ""

    aip.init(project=project, location=location)

    model_resource_name = vertex_model.metadata["resourceName"]
    logger.info("Deploying model: %s", model_resource_name)

    model = aip.Model(model_resource_name)

    endpoints = aip.Endpoint.list(
        filter=f'display_name="{endpoint_name}"',
        project=project,
        location=location,
    )

    if len(endpoints) > 1:
        raise RuntimeError(
            f"Multiple endpoints found with name '{endpoint_name}'. "
            "Please resolve manually."
        )

    endpoint = endpoints[0] if endpoints else None

    if endpoint is None:
        logger.info("No endpoint found, creating: %s", endpoint_name)
        create_kwargs = dict(
            display_name=endpoint_name,
            project=project,
            location=location,
        )
        if enable_request_response_logging:
            # Vertex requires a non-empty BigQuery URI when logging is enabled.
            if not bq_logging_destination_table:
                bq_logging_destination_table = _default_logging_table()
            create_kwargs["enable_request_response_logging"] = True
            create_kwargs[
                "request_response_logging_sampling_rate"
            ] = logging_sampling_rate
            create_kwargs[
                "request_response_logging_bq_destination_table"
            ] = bq_logging_destination_table
        endpoint = aip.Endpoint.create(**create_kwargs)
        logger.info("Created endpoint: %s", endpoint.resource_name)

    deployed_models = endpoint.list_models()

    deploy_kwargs = dict(
        endpoint=endpoint,
        machine_type=machine_type,
        min_replica_count=min_replica_count,
        max_replica_count=max_replica_count,
        service_account=service_account,
        sync=True,
    )
    if not deployed_models:
        logger.info("No models on endpoint, deploying directly")
        deploy_kwargs["traffic_percentage"] = traffic_percentage
    else:
        last_deployed = max(deployed_models, key=lambda dm: dm.create_time)
        logger.info(
            "Rolling deploy: new model gets %d%% traffic, "
            "existing model %s keeps %d%%",
            traffic_percentage,
            last_deployed.id,
            100 - traffic_percentage,
        )
        deploy_kwargs["traffic_split"] = {
            "0": traffic_percentage,
            last_deployed.id: 100 - traffic_percentage,
        }
    model.deploy(**deploy_kwargs)

    deployed_models = sorted(endpoint.list_models(), key=lambda dm: dm.create_time)
    for old_model in deployed_models[:-2]:
        logger.info("Undeploying old model: %s", old_model.id)
        endpoint.undeploy(old_model.id)

    endpoint_id = endpoint.resource_name.split("/")[-1]
    logging_bq_table = _logging_table_uri(endpoint)
    if not logging_bq_table and enable_request_response_logging:
        # Endpoint.create was given this URI when logging was enabled; use it
        # when the SDK does not echo the destination back on the resource.
        if bq_logging_destination_table:
            logging_bq_table = bq_logging_destination_table
        else:
            raise RuntimeError(
                f"Request-response logging was requested but endpoint "
                f"'{endpoint_name}' has no logging destination. Logging can "
                "only be set at endpoint creation time — delete the existing "
                "endpoint and rerun to enable Model Monitoring v2."
            )

    logger.info(
        "Deployment complete on endpoint: %s (id=%s, logging_bq_table=%s)",
        endpoint.resource_name,
        endpoint_id,
        logging_bq_table or "(none)",
    )

    return (endpoint_id, logging_bq_table)
