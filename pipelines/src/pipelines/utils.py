from pathlib import Path
from typing import Any

from jinja2 import Template


def generate_query(file_name: str, folder: Path = None, **replacements: Any) -> str:
    """
    Read input file and replace placeholder using Jinja.

    Args:
        file_name (str): input file to read
        folder (Path): folder which contains file (optional)
        replacements (dict): keyword arguments to use to replace placeholders
    Returns:
        str: replaced content of input file
    """

    if folder is None:
        folder = Path(__file__).parent.parent.parent / "queries"

    with open(folder / file_name, "r") as f:
        query_template = f.read()

    return Template(query_template).render(**replacements)
