from pathlib import Path
from jinja2 import Template


def generate_query(input_file: Path, **replacements) -> str:
    """
    Read input file and replace placeholder using Jinja.

    Args:
        input_file (Path): input file to read
        replacements: keyword arguments to use to replace placeholders
    Returns:
        str: replaced content of input file
    """

    with open(input_file, "r") as f:
        query_template = f.read()

    return Template(query_template).render(**replacements)
