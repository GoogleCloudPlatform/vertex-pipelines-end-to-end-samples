# Copyright 2023 Google LLC

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
	cd pipelines && \
	poetry run pre-commit run --all-files

env ?= dev
AUTO_APPROVE_FLAG :=
deploy: ## Deploy the Terraform infrastructure to your project. Requires VERTEX_PROJECT_ID and VERTEX_LOCATION env variables to be set in env.sh. Optionally specify env=<dev|test|prod> (default = dev)
	@if [ "$(auto-approve)" = "true" ]; then \
		AUTO_APPROVE_FLAG="-auto-approve"; \
	fi; \
	cd terraform/envs/$(env) && \
	terraform init -backend-config='bucket=${VERTEX_PROJECT_ID}-tfstate' && \
	terraform apply -var 'project_id=${VERTEX_PROJECT_ID}' -var 'region=${VERTEX_LOCATION}' $$AUTO_APPROVE_FLAG

undeploy: ## DESTROY the Terraform infrastructure in your project. Requires VERTEX_PROJECT_ID and VERTEX_LOCATION env variables to be set in env.sh. Optionally specify env=<dev|test|prod> (default = dev)
	@if [ "$(auto-approve)" = "true" ]; then \
		AUTO_APPROVE_FLAG="-auto-approve"; \
	fi; \
	cd terraform/envs/$(env) && \
	terraform init -backend-config='bucket=${VERTEX_PROJECT_ID}-tfstate' && \
	terraform destroy -var 'project_id=${VERTEX_PROJECT_ID}' -var 'region=${VERTEX_LOCATION}' $$AUTO_APPROVE_FLAG

install: ## Set up local environment for Python development on pipelines
	@cd pipelines && \
	poetry install --with dev && \
	cd .. && \
	for component_group in components/*/ ; do \
		echo "Setup for $$component_group" && \
		cd "$$component_group" && \
		poetry install --with dev && \
		cd ../.. ;\
	done ; \


compile: ## Compile the pipeline to pipeline.yaml. Must specify pipeline=<training|prediction>
	@cd pipelines/src && \
	poetry run kfp dsl compile --py pipelines/${pipeline}/pipeline.py --output pipelines/${pipeline}/pipeline.yaml --function pipeline

targets ?= training serving
build: ## Build and push training and/or serving container(s) image using Docker. Specify targets=<training serving> e.g. targets=training or targets="training serving" (default)
	@cd model && \
	for target in $$targets ; do \
		echo "Building $$target image" && \
		gcloud builds submit . \
		--region=${VERTEX_LOCATION} \
		--project=${VERTEX_PROJECT_ID} \
		--gcs-source-staging-dir=gs://${VERTEX_PROJECT_ID}-staging/source \
		--substitutions=_DOCKER_TARGET=${target},_DESTINATION_IMAGE_URI=${CONTAINER_IMAGE_REGISTRY}/${target}:${RESOURCE_SUFFIX} ; \
	done 


compile ?= true
build ?= true
wait ?= false
run: ## Run pipeline in sandbox environment. Must specify pipeline=<training|prediction>. Optionally specify wait=<true|false> (default = false). Set compile=false to skip recompiling the pipeline and set build=false to skip rebuilding container images
	@if [ $(compile) = "true" ]; then \
		$(MAKE) compile ; \
	elif [ $(compile) != "false" ]; then \
		echo "ValueError: compile must be either true or false" ; \
		exit ; \
	fi && \
	if [ $(build) = "true" ]; then \
		$(MAKE) build ; \
	elif [ $(build) != "false" ]; then \
		echo "ValueError: build must be either true or false" ; \
		exit ; \
	fi && \
	cd pipelines/src && \
	poetry run python -m pipelines.utils.trigger_pipeline --template_path=pipelines/${pipeline}/pipeline.yaml --display_name=${pipeline} --wait=${wait}

test: ## Run unit tests for a specific component group or for all component groups and the pipeline trigger code. Optionally specify GROUP=<component group e.g. vertex-components>
	@if [ -n "${GROUP}" ]; then \
		echo "Test components under components/${GROUP}" && \
		cd components/${GROUP} && \
		poetry run pytest ; \
	else \
		echo "Testing scripts" && \
		cd pipelines && \
		poetry run python -m pytest tests/utils &&\
		cd .. && \
		for i in components/*/ ; do \
			echo "Test components under $$i" && \
			cd "$$i" && \
			poetry run pytest && \
			cd ../.. ;\
		done ; \
	fi
