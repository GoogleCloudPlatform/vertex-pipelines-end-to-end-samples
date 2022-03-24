from kfp.v2.dsl import Input, Output, Artifact, component, HTML
from pipelines.kfp_components.dependencies import PYTHON37, TENSORFLOW_DATA_VALIDATION


@component(base_image=PYTHON37, packages_to_install=[TENSORFLOW_DATA_VALIDATION])
def visualise_statistics(
    statistics: Input[Artifact],
    view: Output[HTML],
    statistics_name: str = "",
    other_statistics_name: str = "",
    other_statistics_path: str = None,
) -> None:
    """
    Generate an html artifact allowing to visualize the data statistics.
    Args:
        statistics (Input[Artifact]): Generated protobuf statistics from TFDV.
        view (Output[Artifact]): Output artifact to store the visualised statistics
            as html file.
        statistics_name (str): Optional. Name of the statistics. Defaults to ""
        other_statistics_path (str): Optional. Path to other statistics to be
            visualised alongside statistics. Defaults to ""
        other_statistics_name (str): Optional. Name of other statistics.
            Defaults to None.

    Returns:
        None
    """
    import tensorflow_data_validation as tfdv
    from tensorflow_data_validation.utils.display_util import (
        get_statistics_html,
    )

    # load stats
    stats = tfdv.load_statistics(input_path=statistics.path)
    other_stats = None
    if other_statistics_path:
        other_stats = tfdv.load_statistics(input_path=other_statistics_path)

    # create html content
    html = get_statistics_html(
        lhs_statistics=stats,
        lhs_name=statistics_name,
        rhs_statistics=other_stats,
        rhs_name=other_statistics_name,
    )

    # ensure view is stored as html (this will set content-type to text/html)
    if not view.path.endswith(".html"):
        view.path += ".html"

    # write html to output file
    with open(view.path, "w") as f:
        f.write(html)
