<!-- 
Copyright 2022 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
 -->
# TensorFlow Data Validation (TFDV)

## Changing Beam / TFDV versions

To change the version of Apache Beam used in the container, change the base image used in the Dockerfile (`FROM ...`).

To change the version of TFDV used in the container, modify the `pip install` line in the Dockerfile.

Make sure to check the version compatibility in the table [here](https://www.tensorflow.org/tfx/data_validation/install#compatible_versions).

Note: The versions of Apache Beam and TFDV in the container should match those used by the KFP component.

## Building the container

From this directory, run `docker build -t <destination URI> .`

To push the container to the registry, run `docker push <destination URL>`
