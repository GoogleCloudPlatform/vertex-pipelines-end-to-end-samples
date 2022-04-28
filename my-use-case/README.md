# My Use Case

- contains a Python package for custom data science code
- the python code is packaged as a docker container
- kubeflow components are defined using the container as a base image
- this package can be used in pipeline e.g. 

```python
from my_use_case.components import TrainOp

# in the pipeline
train_op = TrainOp(...)
```
