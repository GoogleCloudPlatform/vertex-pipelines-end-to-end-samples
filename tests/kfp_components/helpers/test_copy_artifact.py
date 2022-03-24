from kfp.v2.dsl import Artifact
from pathlib import Path


def test_copy_artifact(tmpdir):
    """
    Test that the source artifact and copy of artifact have the same number of lines
    when copy_artifact IS NOT supplied with a destination uri.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.helpers import copy_artifact

    input_path = Path(tmpdir.join("/input.csv"))
    output_path = Path(tmpdir.join("/output.csv"))
    input_lines = "col1,col2,col3\n1,2,3\n4,5,6"
    input_path.write_text(input_lines)

    # Prepare arguments
    src_artifact = Artifact(uri=input_path)
    des_artifact = Artifact(uri=output_path)

    copy_artifact(
        src_artifact,
        des_artifact,
    )

    output_lines = output_path.read_text()

    assert output_lines == input_lines


def test_copy_artifact_with_destination_uri(tmpdir):
    """
    Test that the source artifact and copy of artifact have the same number of lines
    when copy_artifact IS supplied with a destination uri.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.helpers import copy_artifact

    input_path = Path(tmpdir.join("/input.csv"))
    output_path = Path(tmpdir.join("/output.csv"))

    input_lines = "col1,col2,col3\n1,2,3\n4,5,6"
    input_path.write_text(input_lines)

    # Prepare arguments
    src_artifact = Artifact(uri=input_path)
    des_artifact = Artifact(uri=output_path)
    des_uri = Path(tmpdir.join("destination_uri"))

    copy_artifact(
        src_artifact,
        des_artifact,
        des_uri,
    )

    output_lines = des_uri.read_text()

    assert output_lines == input_lines
