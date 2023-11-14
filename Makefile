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
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

env ?= dev
AUTO_APPROVE_FLAG :=
deploy: ## Deploy infrastructure to your project. Optionally set env=<dev|test|prod> (default = dev).
	@if [ "$(auto-approve)" = "true" ]; then \
		AUTO_APPROVE_FLAG="-auto-approve"; \
	fi; \
	cd terraform/envs/$(env) && \
	terraform init -backend-config='bucket=${VERTEX_PROJECT_ID}-tfstate' && \
	terraform apply -var 'project_id=${VERTEX_PROJECT_ID}' -var 'region=${VERTEX_LOCATION}' $$AUTO_APPROVE_FLAG

undeploy: ## DESTROY the infrastructure in your project. Optionally set env=<dev|test|prod> (default = dev).
	@if [ "$(auto-approve)" = "true" ]; then \
		AUTO_APPROVE_FLAG="-auto-approve"; \
	fi; \
	cd terraform/envs/$(env) && \
	terraform init -backend-config='bucket=${VERTEX_PROJECT_ID}-tfstate' && \
	terraform destroy -var 'project_id=${VERTEX_PROJECT_ID}' -var 'region=${VERTEX_LOCATION}' $$AUTO_APPROVE_FLAG

install: ## Set up local Python environment for development.
	@cd pipelines && \
	poetry install --with dev && \
	cd ../components && \
	poetry install --with dev && \
	cd ../model && \
	poetry install

compile: ## Compile pipeline. Must set pipeline=<training|prediction>.
	@cd pipelines/src && \
	echo "Compiling $$pipeline pipeline" && \
	poetry run kfp dsl compile --py pipelines/${pipeline}.py --output pipelines/${pipeline}.yaml --function pipeline

images ?= training serving
build: ## Build and push container(s). Set images=<training serving> e.g. images=training (default = training serving).
	@cd model && \
	for image in $$images ; do \
		echo "Building $$image image" && \
		gcloud builds submit . \
		--region=${VERTEX_LOCATION} \
		--project=${VERTEX_PROJECT_ID} \
		--gcs-source-staging-dir=gs://${VERTEX_PROJECT_ID}-staging/source \
		--substitutions=_DOCKER_TARGET=$$image,_DESTINATION_IMAGE_URI=${CONTAINER_IMAGE_REGISTRY}/$$image:${RESOURCE_SUFFIX} ; \
	done 

compile ?= true
build ?= true
wait ?= false
run: ## Run pipeline. Must set pipeline=<training|prediction>. Optionally set wait=<true|false> (default = false), compile=<true|false> (default = true) to recompile pipeline, build=<true|false> (default = true) to rebuild container image(s), images=<training serving> (default = training serving) to set which images are rebuilt.
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
	echo "Running $$pipeline pipeline" && \
	poetry run python -m pipelines.utils.trigger_pipeline --template_path=pipelines/${pipeline}.yaml --display_name=${pipeline} --wait=${wait}

training: ## Shortcut to run training pipeline. Rebuilds training and serving images. Supports same options as run.
	$(MAKE) run pipeline=training images=training prediction

prediction:	## Shortcut to run prediction pipeline. Doesn't rebuilt images. Supports same options as run.
	$(MAKE) run pipeline=prediction build=false

components ?= true
test: ## Run unit tests for pipelines. Optionally set components=<true|false> (default = true) to test components package.
	@if [ $(components) = "true" ]; then \
		echo "Running unit tests in components" && \
		cd components && \
		poetry run pytest && \
		cd .. ;  \
	elif [ $(components) != "false" ]; then \
		echo "ValueError: components must be either true or false" ; \
		exit ; \
	fi && \
	echo "Running unit tests in pipelines" && \
	cd pipelines && \
	poetry run python -m pytest

pre-commit: ## Run pre-commit checks for pipelines.
	cd pipelines && \
	poetry run pre-commit run --all-files