# Cloud Function for triggering Vertex Pipelines

This Terraform module deploys a Google Cloud Function that is used to trigger the Vertex Pipeline run. The Cloud Function is triggered by a Pub/Sub message, which is published by Cloud Scheduler.

## Pub/Sub message format

The Pub/Sub message data is a base64-encoded JSON string containing these fields:

```python
{
    "template_path": <Artifact Registry URI pointing to the compiled ML pipeline to run>,
    "enable_caching": <whether to enable/disable pipeline caching. "True" or "False" (omit this field to use default values from pipeline definitions)>,
    "pipeline_parameters": { # Pipeline input parameters
        "foo": "bar",
    }
}
```

To use this module, you just need to provide the Terraform variables - see [scheduling pipelines](/README.md#scheduling-pipelines) in the main README file for more details.

## Development

1. Change the working directory to this directory e.g. `cd terraform/modules/cloudfunction`.
1. Make sure that you are using the correct version of Python that matches `.python-version`. You can use [pyenv](https://github.com/pyenv/pyenv) to manage the different Python versions on your system.
1. Create a new virtual environment `python3 -m venv .venv`.
1. Activate the new virtual environment `source .venv/bin/activate`.
1. Install Python dependencies and dev dependencies `pip install -r src/requirements.txt && pip install -r src/requirements-dev.txt`.
1. To run unit tests, run `PYTHONPATH=. pytest`.
