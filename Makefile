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

-include env.sh
export

help: ## Display this help screen
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
    
pre-commit: ## Runs the pre-commit checks over entire repo
	@cd pipelines && \
	pipenv run pre-commit run --all-files

setup: ## Set up local environment for Python development on pipelines
	@pip install pipenv && \
	cd pipelines && \
	pipenv install --dev

test-trigger: ## Runs unit tests for the pipeline trigger code
	@cd pipelines && \
	pipenv run python -m pytest tests/trigger

compile-pipeline: ## Compile the pipeline to training.json or prediction.json. Must specify pipeline=<training|prediction>
	@cd pipelines/src && \
	pipenv run python -m pipelines.${PIPELINE_TEMPLATE}.${pipeline}.pipeline

setup-components: ## Run unit tests for a component group
	@cd "components/${GROUP}" && \
	pipenv install --dev

setup-all-components: ## Run unit tests for all pipeline components
	@set -e && \
	for component_group in components/*/ ; do \
		echo "Setup components under $$component_group" && \
		$(MAKE) setup-components GROUP=$$(basename $$component_group) ; \
	done

test-components: ## Run unit tests for a component group
	@cd "components/${GROUP}" && \
	pipenv run pytest

test-all-components: ## Run unit tests for all pipeline components
	@set -e && \
	for component_group in components/*/ ; do \
		echo "Test components under $$component_group" && \
		$(MAKE) test-components GROUP=$$(basename $$component_group) ; \
	done

sync-assets: ## Sync assets folder to GCS. Must specify pipeline=<training|prediction>
	@if [ -d "./pipelines/src/pipelines/${PIPELINE_TEMPLATE}/$(pipeline)/assets/" ] ; then \
		echo "Syncing assets to GCS" && \
		gsutil -m rsync -r -d ./pipelines/src/pipelines/${PIPELINE_TEMPLATE}/$(pipeline)/assets ${PIPELINE_FILES_GCS_PATH}/$(pipeline)/assets ; \
	else \
		echo "No assets folder found for pipeline $(pipeline)" ; \
	fi ;

run: ## Compile pipeline, copy assets to GCS, and run pipeline in sandbox environment. Must specify pipeline=<training|prediction>. Optionally specify enable_pipeline_caching=<true|false> (defaults to default Vertex caching behaviour)
	@ $(MAKE) compile-pipeline && \
	$(MAKE) sync-assets && \
	cd pipelines/src && \
	pipenv run python -m pipelines.trigger --template_path=./$(pipeline).json --enable_caching=$(enable_pipeline_caching)

sync_assets ?= true
e2e-tests: ## (Optionally) copy assets to GCS, and perform end-to-end (E2E) pipeline tests. Must specify pipeline=<training|prediction>. Optionally specify enable_pipeline_caching=<true|false> (defaults to default Vertex caching behaviour). Optionally specify sync_assets=<true|false> (defaults to true)
	@if [ $$sync_assets = true ] ; then \
        $(MAKE) sync-assets; \
	else \
		echo "Skipping syncing assets to GCS"; \
    fi && \
	cd pipelines && \
	pipenv run pytest --log-cli-level=INFO tests/${PIPELINE_TEMPLATE}/$(pipeline) --enable_caching=$(enable_pipeline_caching)

env ?= dev
deploy-infra: ## Deploy the Terraform infrastructure to your project. Requires VERTEX_PROJECT_ID and VERTEX_LOCATION env variables to be set in env.sh. Optionally specify env=<dev|test|prod> (default = dev)
	@ cd terraform/envs/$(env) && \
	terraform init -backend-config='bucket=${VERTEX_PROJECT_ID}-tfstate' && \
	terraform apply -var 'project_id=${VERTEX_PROJECT_ID}' -var 'region=${VERTEX_LOCATION}'

destroy-infra: ## DESTROY the Terraform infrastructure in your project. Requires VERTEX_PROJECT_ID and VERTEX_LOCATION env variables to be set in env.sh. Optionally specify env=<dev|test|prod> (default = dev)
	@ cd terraform/envs/$(env) && \
	terraform init -backend-config='bucket=${VERTEX_PROJECT_ID}-tfstate' && \
	terraform destroy -var 'project_id=${VERTEX_PROJECT_ID}' -var 'region=${VERTEX_LOCATION}'
