from kfp.v2.dsl import Input, Model, component
from pipelines.kfp_components.dependencies import PYTHON37


@component(base_image=PYTHON37)
def model_to_uri(model: Input[Model], parent: bool = True) -> str:
    """
    Return the URI of a model.

    Args:
        model (Input[Model]): Input model.
        parent (bool): Whether to return the URI of the parent folder. Defaults to True.

    Returns:
        str: URI of model (or URI of its parent folder).
    """

    uri = model.uri
    if parent:
        uri = uri.rsplit("/", 1)[0]
    return uri
