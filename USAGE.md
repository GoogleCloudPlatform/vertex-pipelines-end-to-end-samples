# USAGE.md 

## Introduction
This document is for users who are editing these templates for their own purposes and would like to add their own pipelines. If you are looking to contribute to the open source templates themselves, please refer to [`CONTRIBUTING`](CONTRIBUTING.md).

## How to add a new pipeline

### Folder structure
Add your new pipeline as a folder under the `pipelines` directory. Within your new pipeline folder you should have two separate folders: `training` and `prediction`. For both `training` and `prediction`, you should include the appropriate `pipeline.py` which describes the structure of the pipeline built from the components under `pipelines/kfp_components/`. The new pipeline folder should also contain the folder `payloads` containing the appropriate payload for triggering. Your pipeline may make use of supporting SQL scripts, and you can store these under a separate folder named `queries`.

See below for an example folder structure:

```
kfp-template-0
│
├── pipelines
│   │
│   ├── new-pipeline
│   │   │
│   │   ├── training
│   │   │   ├── payloads
│   │   │   ├── queries
│   │   │   └── pipeline.py
│   │   │
│   │   └── prediction
│   │       ├── payloads
│   │       ├── queries
│   │       └── pipeline.py

```

### Payload

Please refer to [`README.md`](README.md#pipeline-payload) for more information on how to specify pipeline parameters in the payload file.

## Testing
Please refer to [`CONTRIBUTING.md`](CONTRIBUTING.md#Testing) for information on how to write both unit and end-to-end (E2E) pipeline tests for your pipeline. It is advisable to check that your pipelines pass all tests before being shared with others. 

## Compiling and running your pipeline using the Makefile
To use the same rules listed in the Makefile, you will only need to update the environment variables. In [`.env.sh`](.env.sh), change the value of `PIPELINE_TEMPLATE` to the name of your new pipeline (this should be the same name as the new folder you have created for the pipeline).

If you have organised your pipeline as described [above](#Folder-structure), you should then be able to use the Makefile as usual.

You can compile your pipeline to `training.json` or `prediction.json` with the following command:
```
make compile pipeline=<training|prediction>
```

Or you can compile your pipeline, and then immediately run it with the following command:
```
make run pipeline=<training|prediction>
```
