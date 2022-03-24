from kfp.v2.dsl import Artifact


def test_quote_csv_header(tmpdir):
    """
    Test that quote_csv_header produces an output csv with the correct number of
    lines

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.helpers import quote_csv_header

    input_path = tmpdir.join("/input.csv")
    output_path = tmpdir.join("/output.csv")

    input_lines = """feature1,feature2,feature3
1,2,3
4,5,6
"""

    input_path.write_text(input_lines, "utf-8")

    input = Artifact(uri=input_path)
    output = Artifact(uri=output_path)

    quote_csv_header(input, output)

    output_lines = output_path.readlines()

    assert output_lines[0] == '"feature1","feature2","feature3"\n'
    assert len(output_lines) == 3


def test_header_only_quote_csv_header(tmpdir):
    """
    Test that quote_csv_header successfully produces a header row with double
    quoted column names when passed a csv with only a header.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    # test for when the input only has one row (headers only)
    from pipelines.kfp_components.helpers import quote_csv_header

    # create a csv with only a single header row
    input_line = """feature1,feature2,feature3"""

    input_path = tmpdir.join("/input_header_only.csv")
    output_path = tmpdir.join("/output_header_only.csv")

    input_path.write_text(input_line, "utf-8")

    input_header_only = Artifact(uri=input_path)
    output_header_only = Artifact(uri=output_path)

    quote_csv_header(input_header_only, output_header_only)

    output_lines = output_path.readlines()

    assert output_lines[0] == '"feature1","feature2","feature3"\n'
    assert len(output_lines) == 1


def test_empty_quote_csv_header(tmpdir):
    """
    Test that quote_csv_header successfully produces a single line csv with the
    expected double quoted output when provided with an empty input.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.helpers import quote_csv_header

    # create an empty input
    input_line = """"""

    input_path = tmpdir.join("/input_empty.csv")
    output_path = tmpdir.join("/output_empty.csv")

    input_path.write_text(input_line, "utf-8")

    input_empty = Artifact(uri=input_path)
    output_empty = Artifact(uri=output_path)

    quote_csv_header(input_empty, output_empty)

    output_lines = output_path.readlines()

    assert len(output_lines) == 1
    assert output_lines[0] == '""\n'
