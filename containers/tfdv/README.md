# TensorFlow Data Validation (TFDV)

## Changing Beam / TFDV versions

To change the version of Apache Beam used in the container, change the base image used in the Dockerfile (`FROM ...`).

To change the version of TFDV used in the container, modify the `pip install` line in the Dockerfile.

Make sure to check the version compatibility in the table [here](https://www.tensorflow.org/tfx/data_validation/install#compatible_versions).

Note: The versions of Apache Beam and TFDV in the container should match those used by the KFP component.

## Building the container

From this directory, run `docker build -t <destination URI> .`

To push the container to the registry, run `docker push <destination URL>`
