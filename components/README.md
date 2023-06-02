# Kubeflow Pipelines Components

This directory contains multiple Python packages that are used to define pipeline components with the Kubeflow Pipelines SDK. Each subdirectory is a package with its own set of Python dependencies. Components with the same Python dependencies can reside in the same package, but components with different Python dependencies should be split into different Python packages.

## Creating a new pipeline components package

To create a new set of components (with different Python dependencies), copy one of the existing subdirectories and rename the different files and directories as appropriate (e.g. `vertex-components` -> `my-new-components`). You will also need to update any references in the Python files themselves, as well as `poetry.lock` and `pyproject.toml`.

Your Python dependencies should be defined in `poetry.lock`, `pyproject.toml`, and in `packages_to_install` (in the `@component` decorator):

- In `pyproject.toml`, add `kfp` to the `[dependencies]` section (pinned to a specific version), and add any dependencies that your component uses under `[tool.poetry.dependencies]`(each pinned to a specific version)
- In `packages_to_install` (in the `@component` decorator used to define your component), add any dependencies that your component uses (each pinned to a specific version)

Define your pipeline components using the `@component` decorator in Python files under `my-new-components/src/my-new-components`. You will need to update the `__init__.py` file to provide tests - see the [Kubeflow Pipelines documentation](https://www.kubeflow.org/docs/components/pipelines/v1/sdk-v2/python-function-components/#building-python-function-based-components) for more information about writing pipeline components.

Finally, you will need to install this new components package into the [`pipelines`](../pipelines) package. In [`pipelines/pyproject.toml`](../pipelines/pyproject.toml), add the following line to the `tool.poetry.dependencies` section:

```
my-new-components = { path = "../components/my-new-components", develop = true }
```
Once you have added this line to [`pipelines/pyproject.toml`](../pipelines/pyproject.toml), run `make setup` from the root of the repository to install the new components package into the `pipelines` package.

## Testing components

Unit tests for components are defined using pytest and should be created under `my-new-components/tests`. Take a look at the existing components to see examples of how you can write these tests and perform mocking/patching of KFP Artifact types.

To run the unit tests, you will first need to set up the virtual environment for the new components by running `make setup-components GROUP=my-new-components` from the root of the repository. Once you have done this, you can run the unit tests using `make test-components GROUP=my-new-components`.
