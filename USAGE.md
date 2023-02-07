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
 # USAGE.md 

## Introduction
This document is for users who are editing these templates for their own purposes and would like to add their own pipelines. If you are looking to contribute to the open source templates themselves, please refer to [`CONTRIBUTING`](CONTRIBUTING.md).

## How to add a new pipeline

### Folder structure
Add your new pipeline as a folder under the `pipelines` directory. Within your new pipeline folder you should have two separate folders: `training` and `prediction`. For both `training` and `prediction`, you should include the appropriate `pipeline.py` which describes the structure of the pipeline built from the components under `pipelines/kfp_components/`. Your pipeline may make use of supporting SQL scripts, and you can store these under a separate folder named `queries`.

See below for an example folder structure:

```
kfp-template-0
│
├── pipelines
│   │
│   ├── new-pipeline
│   │   │
│   │   ├── training
│   │   │   ├── queries
│   │   │   └── pipeline.py
│   │   │
│   │   └── prediction
│   │       ├── queries
│   │       └── pipeline.py

```

## Testing
Please refer to [`CONTRIBUTING.md`](CONTRIBUTING.md#Testing) for information on how to write both unit and end-to-end (E2E) pipeline tests for your pipeline. It is advisable to check that your pipelines pass all tests before being shared with others. 

## Compiling and running your pipeline using the Makefile
To use the same rules listed in the Makefile, you will only need to update the environment variables. In [`.env.sh`](.env.sh), change the value of `PIPELINE_TEMPLATE` to the name of your new pipeline (this should be the same name as the new folder you have created for the pipeline).

If you have organised your pipeline as described [above](#Folder-structure), you should then be able to use the Makefile as usual.

Before compiling your pipeline, make sure to re-compile your pipeline components if you have made any changes:

```
make compile-components GROUP=<component group e.g. aiplatform>
```

Or to re-compile all pipeline components to YAML:
```
make compile-all-components
```

You can compile your pipeline to `training.json` or `prediction.json` with the following command:
```
make compile pipeline=<training|prediction>
```

Or you can compile your pipeline, and then immediately run it with the following command:
```
make run pipeline=<training|prediction>
```
