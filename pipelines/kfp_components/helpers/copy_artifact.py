from kfp.v2.dsl import Artifact, Input, Output, component
from pipelines.kfp_components.dependencies import PYTHON37


@component(base_image=PYTHON37)
def copy_artifact(
    src_artifact: Input[Artifact], des_artifact: Output[Artifact], des_uri: str = None
) -> None:
    """
    Copy artifact.

    Args:
        src_artifact (Input[Artifact]): Source artifact.
        des_artifact (Output[Artifact]): Copy of artifact
        des_uri (str): Optional. Set destination URI of copied artifact which includes
            the artifact itself. Defaults to None.

    Returns:
        None
    """
    import shutil
    from pathlib import Path

    if des_uri is not None:
        des_artifact.uri = des_uri

    # ensure parent folder(s) exist
    Path(des_artifact.path).parent.mkdir(parents=True, exist_ok=True)

    # copy artifact
    shutil.copy(src_artifact.path, des_artifact.path)
