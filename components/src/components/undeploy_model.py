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

from kfp.dsl import component


@component(
    base_image="python:3.12.8",
    packages_to_install=[
        "google-cloud-aiplatform==1.135.0",
    ],
)
def undeploy_model(
    project: str,
    location: str,
    endpoint_id: str,
    deployed_model_id: str = "",
    delete_endpoint_if_empty: bool = False,
) -> None:
    """
    Undeploy model(s) from a Vertex AI endpoint and optionally clean up
    the endpoint.

    Can undeploy all models on the endpoint (when deployed_model_id is empty)
    or a single deployed model by ID.

    Args:
        project: GCP project ID.
        location: GCP region (e.g. europe-west2).
        endpoint_id: Vertex AI endpoint ID (e.g. from deploy_model output).
        deployed_model_id: If set, undeploy only this deployed model ID;
            otherwise undeploy all models on the endpoint.
        delete_endpoint_if_empty: If True, after undeploying, delete the
            endpoint when it has no deployed models left.
    """
    import logging

    import google.cloud.aiplatform as aip

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    aip.init(project=project, location=location)

    endpoint_resource_name = (
        f"projects/{project}/locations/{location}/endpoints/{endpoint_id}"
    )
    logger.info("Loading endpoint: %s", endpoint_resource_name)
    endpoint = aip.Endpoint(endpoint_resource_name)

    deployed_models = endpoint.list_models()
    if not deployed_models:
        logger.info(
            "Endpoint has no deployed models, nothing to undeploy (step completes successfully). "
            "This can happen if pipeline caching reused a previous deploy step and the endpoint was "
            "already undeployed in an earlier run. Use cache=false to force a fresh deploy before undeploy."
        )
    else:
        if deployed_model_id:
            ids_to_undeploy = [deployed_model_id]
            if not any(dm.id == deployed_model_id for dm in deployed_models):
                raise ValueError(
                    f"Deployed model id '{deployed_model_id}' not found on endpoint. "
                    f"Current deployed model ids: {[dm.id for dm in deployed_models]}"
                )
        else:
            ids_to_undeploy = [dm.id for dm in deployed_models]

        undeployed = set()
        for did in ids_to_undeploy:
            logger.info("Undeploying model: %s", did)
            remaining = [
                dm for dm in deployed_models
                if dm.id != did and dm.id not in undeployed
            ]
            if not remaining:
                endpoint.undeploy(did)
            else:
                total = 100
                traffic_split = {dm.id: total // len(remaining) for dm in remaining}
                traffic_split[remaining[0].id] += total - sum(traffic_split.values())
                endpoint.undeploy(did, traffic_split=traffic_split)
            undeployed.add(did)

    if delete_endpoint_if_empty:
        endpoint = aip.Endpoint(endpoint_resource_name)
        if not endpoint.list_models():
            logger.info("Deleting empty endpoint: %s", endpoint_resource_name)
            endpoint.delete()
        else:
            logger.info(
                "Endpoint still has deployed models, not deleting endpoint"
            )
