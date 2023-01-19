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
    
pre-commit: ## Runs the pre-commit over entire repo
	@pipenv run pre-commit run --all-files

unit-tests: ## Runs unit tests for kfp_components
	@pipenv run python -m pytest tests/kfp_components

trigger-tests: ## Runs unit tests for the pipeline trigger code
	@pipenv run python -m pytest tests/trigger

compile: ## Compile the pipeline to training.json or prediction.json. Must specify pipeline=<training|prediction>
	@pipenv run python -m pipelines.${PIPELINE_TEMPLATE}.${pipeline}.pipeline

sync-assets: ## Sync assets folder to GCS. Must specify pipeline=<training|prediction>
	@gsutil -m rsync -r -d ./pipelines/${PIPELINE_TEMPLATE}/$(pipeline)/assets ${PIPELINE_FILES_GCS_PATH}/$(pipeline)/assets

run: ## Compile pipeline, copy assets to GCS, and run pipeline in sandbox environment. Must specify pipeline=<training|prediction>. Optionally specify enable_pipeline_caching=<true|false> (defaults to default Vertex caching behaviour)
	@ $(MAKE) compile && \
	$(MAKE) sync-assets && \
	pipenv run python -m pipelines.trigger.main --template_path=./$(pipeline).json --enable_caching=$(enable_pipeline_caching)

e2e-tests: ## Compile pipeline, copy assets to GCS, and perform end-to-end (E2E) pipeline tests. Must specify pipeline=<training|prediction>. Optionally specify enable_pipeline_caching=<true|false> (defaults to default Vertex caching behaviour)
	@ $(MAKE) compile && \
	$(MAKE) sync-assets && \
	pipenv run python -m pytest --log-cli-level=INFO tests/${PIPELINE_TEMPLATE}/$(pipeline) --enable_caching=$(enable_pipeline_caching)
