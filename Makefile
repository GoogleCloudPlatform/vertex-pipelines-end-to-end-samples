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

help: ## Display this help screen.
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

env ?= dev
AUTO_APPROVE_FLAG :=
deploy: ## Deploy infrastructure to your project. Optionally set env=<dev|test|prod> (default=dev).
	@echo "################################################################################" && \
	echo "# Deploy $$env environment" && \
	echo "################################################################################" && \
	if [ "$(auto-approve)" = "true" ]; then \
		AUTO_APPROVE_FLAG="-auto-approve"; \
	fi; \
	cd terraform/envs/$(env) && \
	terraform init -backend-config='bucket=${VERTEX_PROJECT_ID}-tfstate' && \
	terraform apply -var 'project_id=${VERTEX_PROJECT_ID}' -var 'region=${VERTEX_LOCATION}' $$AUTO_APPROVE_FLAG

undeploy: ## Destroy the infrastructure in your project. Optionally set env=<dev|test|prod> (default=dev).
	@echo "################################################################################" && \
	echo "# Destroy $$env environment" && \
	echo "################################################################################" && \
	if [ "$(auto-approve)" = "true" ]; then \
		AUTO_APPROVE_FLAG="-auto-approve"; \
	fi; \
	cd terraform/envs/$(env) && \
	terraform init -backend-config='bucket=${VERTEX_PROJECT_ID}-tfstate' && \
	terraform destroy -var 'project_id=${VERTEX_PROJECT_ID}' -var 'region=${VERTEX_LOCATION}' $$AUTO_APPROVE_FLAG

install: ## Set up local Python environment for development.
	@echo "################################################################################" && \
	echo "# Install Python dependencies" && \
	echo "################################################################################" && \
	cd model && \
	poetry install --no-root && \
	cd ../pipelines && \
	poetry install --with dev && \
	cd ../components && \
	poetry install --with dev

compile: ## Compile pipeline. Set pipeline=<training|prediction>.
	@echo "################################################################################" && \
	echo "# Compile $$pipeline pipeline" && \
	echo "################################################################################" && \
	cd pipelines/src && \
	poetry run kfp dsl compile --py pipelines/${pipeline}.py --output pipelines/${pipeline}.yaml --function pipeline

images ?= training prediction
build: ## Build and push container(s). Set images=<training and/or prediction> (default="training prediction").
	@echo "################################################################################" && \
	echo "# Build $$images image(s)" && \
	echo "################################################################################" && \
	cd model && \
	for image in $$images ; do \
		echo "Build $$image image" && \
		gcloud builds submit . \
		--region=${VERTEX_LOCATION} \
		--project=${VERTEX_PROJECT_ID} \
		--gcs-source-staging-dir=gs://${VERTEX_PROJECT_ID}-staging/source \
		--substitutions=_DOCKER_TARGET=$$image,_DESTINATION_IMAGE_URI=${CONTAINER_IMAGE_REGISTRY}/$$image:${RESOURCE_SUFFIX} \
		--suppress-logs ; \
	done 

compile ?= true
build ?= true
cache ?= true
wait ?= false
run: ## Run a pipeline. Set pipeline=<training|prediction>. Optionally set compile=<true|false> (default=true), build=<true|false>, cache=<true|false> (default=true). wait=<true|false> (default=false).
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
	echo "################################################################################" && \
	echo "# Run $$pipeline pipeline" && \
	echo "################################################################################" && \
	cd pipelines/src && \
	ENABLE_PIPELINE_CACHING=$$cache poetry run python -m pipelines.utils.trigger_pipeline \
		--template_path=pipelines/${pipeline}.yaml --display_name=${pipeline} --wait=${wait}

training: ## Run training pipeline. Rebuilds training and prediction images. Supports same options as run.
	@$(MAKE) run pipeline=training

prediction:	## Run prediction pipeline. Doesn't rebuilt images. Supports same options as run.
	@$(MAKE) run pipeline=prediction build=false

packages ?= pipelines components
test: ## Run unit tests. Optionally set packages=<pipelines and/or components> (default="pipelines components").
	@echo "################################################################################" && \
	echo "# Test $$packages package(s)" && \
	echo "################################################################################" && \
	for package in $$packages ; do \
		echo "Testing $$package package" && \
		cd $$package && \
		poetry run pytest && \
		cd .. ; \
	done

pre-commit: ## Run pre-commit checks for pipelines.
	@cd pipelines && \
	poetry run pre-commit run --all-files
