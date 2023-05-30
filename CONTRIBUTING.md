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
 # Contributing

Welcome to the Vertex Templates Project, and thank you for your interest in contributing! 

This guide is chiefly for users wishing to contribute to the opensource version. Those who want to edit the templates to suit their own purposes should look at [USAGE](USAGE.md), but may find some sections useful.

## Links to Important Resources
- [pytest](https://docs.pytest.org)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [poetry](https://python-poetry.org/docs/#installation)
- [Kubeflow Pipelines](https://www.kubeflow.org/docs/components/pipelines/overview)
- [Vertex AI](https://cloud.google.com/vertex-ai/docs)
- [AI Platform SDK](https://googleapis.dev/python/aiplatform/latest/index.html)

## Python code guidelines

### Code linting and formatting
We use linting to highlight problems in our Python code which could later produce errors or affect efficiency. For example, linting detects things such as uninitialised or undefined variables, unused imported modules, and missing parentheses. To detect and enact fixes to these problems, we make use of the Python linter: [Flake8](https://flake8.pycqa.org/en/latest/) and the formatter [Black](https://black.readthedocs.io/en/stable/). These are run as part of our [pre-commit checks](#Pre-commit-checks). We have some configurations for Flake8 that you can find [here](.flake8).
### Docstring format
Please include docstrings that are compliant with the [Google Style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).

In brief, the docstring is a triple quoted string placed immediately after the function definition and should contain:
- A brief description of the function
- A section `Args:` where you list the function arguments
  - For each argument, include the argument type in brackets
- A section `Returns:` where you list what the function returns
  - For each returned item, include the type
## Testing
Testing is an important way for us to check that our code works as expected and forms a key part of our CI/CD strategy. For example, pull requests will not pass our checks if any unit tests fail. You should therefore ensure that your pull request passes all tests before merging.

### Unit Tests

We use unit tests to test small sections of logically isolated code in our pipeline components.

#### Mocking & patching
When we test a function that makes an external API call (for example to a service on GCP), we mock the associated module or class and its functions and attributes. The rationale behind this is that we want to test our own logic and not the API call(s) themselves. Indeed, API calls can be broken, computationally expensive, slow, or limited, and we do not want our unit tests to fail because of any of these. 

We do mocking/patching in two different ways:
1. [`monkeypatch`](https://docs.pytest.org/en/6.2.x/monkeypatch.html): this built-in `pytest` fixture allows you to modify an attribute (such as an instance method in a class). We use `monkeypatch` only in the relevant `conftest.py` file for the fixtures that are applied before every unit test. We have used `monkeypatch` in the following fixtures:
    - `mock_kfp_artifact`: used to mock the `Artifact` object (and thus any derived classes such as `Dataset`, `Model`, etc.) in `kfp.v2.dsl` to return the URI as
    the path. This lets us create mock Artifact objects locally for our unit tests.
2. `unittest.mock.patch`: this object in the `unittest` library enables us to mock classes (and its associated attributes and methods) within a context manager. We use `mock.patch` inside the individual test scripts to mock object(s) that are used in the function being tested. This allows us to replace the target class/object with a Mock object, ultimately allowing us to make assertions on how this Mock object has been used. For example, the `assert_called_once_with` method allows us to check that a specific method of a Mock object was called once with specific arguments. Alternatively, we can set the attributes of our Mock objects to specific values, and assert that the component logic being tested handles these cases correctly (e.g. by raising a `ValueError`). An example of using the `mock.patch` context manager is in [`test_lookup_model.py`](tests/kfp_components/aiplatform/test_lookup_model.py) for [`lookup_model.py`](./pipeline_components/aiplatform/aiplatform/lookup_model/component.py), where there is an API call to list models (in Vertex AI) based on a filter, namely `google.cloud.aiplatform.Model.list`. When we test this KFP component, we are not interested in actually making this API call, so instead we mock it. We do this by mocking the `google.cloud.aiplatform.Model` class:
```
with mock.patch("google.cloud.aiplatform.Model") as mock_model:

    # Mock attribute and method
    mock_model.resource_name = "my-model-resource-name"
    mock_model.list.return_value = [mock_model]

    # Invoke the model look up
    found_model_resource_name = lookup_model(
        model_name="my-model",
        project_location="europe-west4",
        project_id="my-project_id",
        order_models_by="create_time desc",
        fail_on_model_not_found=False,
    )

    assert found_model_resource_name == "my-model-resource-name"
```

#### `pytest` fixtures & `conftest.py`
- `tmpdir`: a built-in `pytest` fixture that we use to create temporary paths for our unit tests.
- `monkeypatch`: see above.
- The file `conftest.py` contains our custom `pytest` fixtures which we apply for each testing session. 

#### How to write unit tests
Some things to consider testing for in your code:
- **Do you have any logical conditions?** Consider writing tests that assert the desired outcome occurs for each possible outcome. In particular, you can assert that a certain error is raised in your function under certain conditions. For example, in [`lookup_model.py`](./pipeline_components/aiplatform/aiplatform/lookup_model/component.py), the function `lookup_model` raises a `RuntimeError` if no models are found:
```
if fail_on_model_not_found:
    raise RuntimeError(f"Failed as model not found")
```
Now in [`test_lookup_model.py`](./pipeline_components/aiplatform/tests/test_lookup_model.py), in the unit test `test_lookup_model_when_no_models_fail` you can use `pytest.raises` to check that `lookup_model` actually raises a `RuntimeError`:
```
with pytest.raises(RuntimeError):
    lookup_model(
        model_name="my-model",
        project_location="europe-west4",
        project_id="my-project-id",
        order_models_by="create_time desc",
        fail_on_model_not_found=True,
    )
```

#### How to run unit tests
Unit tests for pipeline components are run automatically on each pull request. You can also run them on your local machine:
```
make test-all-components
```

Or to just run the unit tests for a given component group (e.g. `aiplatform`):
```
make test-components GROUP=vertex-components
```

### End-to-end (E2E) pipeline tests
We use End-to-end (E2E) pipeline tests to ensure that our pipelines are running as expected. Our E2E tests ensure:
- That the pipeline is successfully triggered locally, and that the pipeline run is completed
- That common tasks(components), which are stored in a dictionary object (`common_tasks`), occurred in the pipeline
- That if any task in a conditional tasks dictionary object occurred in the pipeline, the remaining tasks based on that condition should have all occurred as well
- That these pipeline tasks output the correct artifacts, by checking whether they have been saved to a GCS URI or have been generated successfully in Vertex AI.

Note:
These dictionary objects (`common_tasks`, `conditional_tasks`) are defined in `test_e2e.py` in each pipeline folder e.g (`./pipelines/tests/xgboost/training/test_e2e.py`). 
The E2E test only allows one common tasks group but the number of conditional tasks group is not limited. To define the correct task group, 
please go to pipeline job on Vertex AI for more information. 
For example, in the XGBoost training pipeline, we have two conditional tasks groups that are bounded in the dashed frame. 
Thus, in `./pipelines/tests/xgboost/training/test_e2e.py`, there are two dictionaries of two conditional tasks group.

- Optionally check for executed tasks and created output artifacts.

#### How to run end-to-end (E2E) pipeline tests
E2E tests are run on each PR that is merged to the main branch. You can also run them on your local machine: 
```
make e2e-tests pipeline=<training|prediction>
```

### How to adapt the end-to-end (E2E) pipeline tests for your own pipeline
As described above, we provide our E2E tests with a dictionary of expected outputs for the pipeline components, and confirm that these outputs are stored in a GCS uri or generated successfully in Vertex AI.
 For information on how tasks and outputs are stored in your pipeline, we recommend looking at these [AI Platform documents](https://googleapis.dev/python/aiplatform/latest/aiplatform_v1beta1/types.html#google.cloud.aiplatform_v1beta1.types.PipelineJob). The following briefly describes how we created this dictionary, and you can use this to create your own dictionary of expected tasks:
1. Trigger a pipeline (using the default pipeline input parameters), and collect the pipeline tasks and their details. For example:
```
from trigger.main import trigger_pipeline_from_payload

...

    payload = {
        "attributes": {
            "template_path": template_path,
            "enable_caching": False
        }
    }
    pl = trigger_pipeline_from_payload(payload)
    pl.wait()
    details = pl.to_dict()
    tasks = details["jobDetail"]["taskDetails"]

```
2. Check missing tasks by comparing the actual task produced in pipeline and the expected tasks defined in each pipeline test file ( e.g `./pipelines/tests/xgboost/training/test_e2e.py`))
```
    missing_tasks = [
        task_name
        for task_name in expected_tasks.keys()
        if task_name not in actual_tasks.keys()
    ]
```
3. Check all tasks outputs are as expected and accessible
```
    storage_client = storage.Client()
    # 2. Missing outputs check
    for task_name, expected_output in expected_tasks.items():
        actual_outputs = actual_tasks[task_name]
        # 2-2. if the output artifact are as expected
        diff = set(expected_output).symmetric_difference(actual_outputs.keys())
        assert (
            len(diff) == 0
        ), f"task: {task_name}, expected_output {expected_output}, actual_outputs: {actual_outputs.keys()}"
        for output_artifact in expected_output:
            output_uri = actual_outputs[output_artifact]

            # 2-2. if output is generated successfully
            # for all gcs uri check its file size
            if output_uri.startswith("gs://"):
                file_size = test_gcs_uri(output_uri, storage_client)
                assert (
                    file_size > 0
                ),  f"{output_artifact} in task {task_name} is not accessible"
            # for Vertex resource check if the resource exists
            else: 
                # all Vertex AI resource uri following this pattern: 
                # ‘projects/<my-project>/locations/<location>/<resource_type>/<resource_name>’
                artifact_type = output_uri.split('/')[-2] 
                object_existence = test_functions[artifact_type](output_uri.split('/')[-1])
                assert (
                    object_existence
                ), f"{output_artifact} in task {task_name} is not accessible"

```
Notes:
This template only provides three Vertex AI resource check functions: `test_vertex_model_uri`,`test_vertex_endpoint_uri`,`test_batch_prediction_job_uri`. 
For other Vertex artifacts, you can create a new one following this code:
```
def test_vertex_endpoint_uri(output_uri: str):
    from google.cloud.aiplatform import Model
    try: 
        Model(
            endpoint_name=output_uri,
            project=project_id,
            location=project_location,
        )
        return True
    except:
        return False

```

## Adding or changing python dependencies
We use [poetry](https://python-poetry.org/docs/#installation) to handle our packages and their dependencies. Each group of pipeline components (e.g. [vertex](./components/vertex-components/)) includes its own poetry environment, and there is a [separate poetry environment](./pipelines/) for the ML pipelines themselves and the pipeline trigger code.

### Adding python dependencies
You may need to add new packages for your own use cases. To do this, run the following from the relevant directory ([pipelines](./pipelines) for the main ML pipeline dependencies or the directory of the relevant component group e.g. [aiplatform](./pipeline_components/aiplatform/)):
```
poetry install <package name>
```

## Committing Changes

### Add changed files to staging area
```
git add <path(s) of changed file(s)>
```
### Commit messages
To allow others (and yourself!) to understand your changes easily, we encourage writing detailed commit messages. We use [Commitizen](https://commitizen-tools.github.io/commitizen/) as a guide. In brief, all commit messages should start with one of the following prefixes:
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons etc)
- **refactor**: A change that neither fixes a bug or adds a feature
- **perf**: A change that improves performance
- **test**: Add new tests or correct existing tests
- **build**: Changes that affect the build system or external dependencies (e.g. pip, docker, npm)
- **ci**: Changes to CI configuration files and scripts

After the prefix, you can specify the scope (e.g. the class or file name) of the change in brackets. Finally, you include the details of the change. For example
```
git commit -s -m"prefix(scope): message here"
```

### Things to avoid in your commit messages:
- Too brief or non-specific messages (e.g. `bug fix`, `small changes`)
- Commit message does not explain why changes were made


### Pre-commit checks
We use pre-commit hooks to automatically identify and correct issues in code. You can find the details of the hooks we use [here](.pre-commit-config.yaml). If any of these fail, the commit will be unsuccessful and you will be able to see which hook failed and some additional details in your terminal.

To run the pre-commit hooks over the entire repo, run:
```
make pre-commit
```

#### What to do if pre-commit checks fail:
- **Checks fail and the pre-commit hook edits a file to fix the error**. Sometimes the pre-commit hook will identify an error (e.g. the absence of a blank line at the end of a file), and will correct this automatically by changing your file. You will then need to re-add these files to the staging area before trying to commit again.
- **Checks fail and displays an error message**. Some errors cannot be automatically fixed by pre-commit hooks, and instead they will display the error number and the file and line which failed. For more details beyond the error message, you can look up the error number online. The most common errors are caused by lines which exceed the character limit. Once you identify the cause of the error, you will need to fix this in your code, add the edited file to the staging area, and then commit again.

### Commit changes to Python packages and dependencies
If you have changes to `pyproject.toml` and `poetry.lock`, please make sure you commit these files!

## Makefile
This project contains a [Makefile](Makefile) which contains "rules" describing the commands to be executed by the system. These allow you to quickly and easily run commands for specific purposes, for example running all of the unit-tests, or compiling a pipeline. You can find the full set of available `make` rules by running:
```
make help
```

Some of these rules use the environment variables specified in [`env.sh`](env.sh).

**It is not expected that you will need to change the Makefile or create a new one.**

## Assets folder

For a brief description of the Assets folder, please refer to our [general documentation](README.md#Assets). 
To make sure that assets are available while running the ML pipelines, `make run` ensure that these will be uploaded automatically to the respective Google Cloud Storage locations.

### Common assets

Within the [assets](./assets/) folder, there are common files stored which need to be uploaded to Google Cloud Storage so that the pipelines running Vertex AI can consume such assets, namely:
