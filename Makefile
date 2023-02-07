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

test-trigger: ## Runs unit tests for the pipeline trigger code
	@cd pipelines && \
	pipenv install --dev && \
	pipenv run python -m pytest tests/trigger

compile-pipeline: ## Compile the pipeline to training.json or prediction.json. Must specify pipeline=<training|prediction>
	@cd pipelines && \
	pipenv run python -m pipelines.${PIPELINE_TEMPLATE}.${pipeline}.pipeline

compile-components: ## Compile all the components in a component group
	@cd pipeline_components/${GROUP} && \
	pipenv install && \
	for component in ${GROUP}/*/component.py ; do \
		pipenv run python $$component ; \
	done

compile-all-components: ## Compile all pipeline components
	@set -euo pipefail && \
	for component_group in pipeline_components/*/ ; do \
		echo "Compiling components under $$component_group" && \
		$(MAKE) compile-components GROUP=$$(basename $$component_group) ; \
	done

test-components: ## Run unit tests for a component group
	@cd pipeline_components/${GROUP} && \
	pipenv install --dev && \
	pipenv run pytest

test-all-components: ## Run unit tests for all pipeline components
	@set -euo pipefail && \
	for component_group in pipeline_components/*/ ; do \
		echo "Running unit tests for components under $$component_group" && \
		$(MAKE) test-components GROUP=$$(basename $$component_group) ; \
	done

sync-assets: ## Sync assets folder to GCS. Must specify pipeline=<training|prediction>
	@gsutil -m rsync -r -d ./pipelines/pipelines/${PIPELINE_TEMPLATE}/$(pipeline)/assets ${PIPELINE_FILES_GCS_PATH}/$(pipeline)/assets

run: ## Compile pipeline, copy assets to GCS, and run pipeline in sandbox environment. Must specify pipeline=<training|prediction>. Optionally specify enable_pipeline_caching=<true|false> (defaults to default Vertex caching behaviour)
	@ $(MAKE) compile-pipeline && \
	$(MAKE) sync-assets && \
	cd pipelines && \
	pipenv run python -m trigger.main --template_path=./$(pipeline).json --enable_caching=$(enable_pipeline_caching)

e2e-tests: ## Compile pipeline, copy assets to GCS, and perform end-to-end (E2E) pipeline tests. Must specify pipeline=<training|prediction>. Optionally specify enable_pipeline_caching=<true|false> (defaults to default Vertex caching behaviour)
	@ $(MAKE) compile-pipeline && \
	$(MAKE) sync-assets && \
	cd pipelines && \
	pipenv run python -m pytest --log-cli-level=INFO tests/${PIPELINE_TEMPLATE}/$(pipeline) --enable_caching=$(enable_pipeline_caching)
