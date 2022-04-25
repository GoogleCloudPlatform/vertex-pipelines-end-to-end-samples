import tensorflow_data_validation as tfdv
from kfp.v2.dsl import Artifact


def test_visualise_statistics(tmpdir, make_csv_file):
    """
    Assert that the artifact produced by visualise_statistics exists.

    Args:
        tmpdir: pytest tmpdir fixture
        make_csv_file: pytest fixture defined in conftest.py

    Returns:
        None
    """
    from pipelines.kfp_components.tfdv import visualise_statistics

    data_path = str(tmpdir.join("sample.csv"))
    stats_path = tmpdir.join("sample.stats")
    view_path = tmpdir.join("stats_view.html")

    make_csv_file(10, 100, data_path)

    tfdv.write_stats_text(tfdv.generate_statistics_from_csv(data_path), str(stats_path))

    statistics = Artifact(uri=stats_path)
    view = Artifact(uri=str(view_path))

    visualise_statistics(statistics, view)

    assert view_path.exists()


def test_visualise_statistics_append_html(tmpdir, make_csv_file):
    """
    Assert that the output produced by visualise_statistics is an HTML artifact
    (i.e. ends with ".html").

    Args:
        tmpdir: pytest tmpdir fixture
        make_csv_file: pytest fixture defined in conftest.py

    Returns:
        None
    """
    from pipelines.kfp_components.tfdv import visualise_statistics

    data_path = str(tmpdir.join("sample.csv"))
    stats_path = tmpdir.join("sample.stats")
    view_path = tmpdir.join("stats_view")  # without .html

    make_csv_file(10, 100, data_path)

    tfdv.write_stats_text(tfdv.generate_statistics_from_csv(data_path), str(stats_path))

    statistics = Artifact(uri=stats_path)
    view = Artifact(uri=str(view_path))

    visualise_statistics(statistics, view)

    assert view.path.endswith(".html")


def test_visualise_two_statistics(tmpdir, make_csv_file):
    """
    Assert that the artifact produced by visualise_statistics exists when supplied
    with two statistics paths to display.

    Args:
        tmpdir: pytest tmpdir fixture
        make_csv_file: pytest fixture defined in conftest.py

    Returns:
        None
    """
    from pipelines.kfp_components.tfdv import visualise_statistics

    data_path = str(tmpdir.join("sample.csv"))
    stats_path = tmpdir.join("sample.stats")
    view_path = tmpdir.join("stats_view.html")

    make_csv_file(10, 100, data_path)

    tfdv.write_stats_text(tfdv.generate_statistics_from_csv(data_path), str(stats_path))

    statistics = Artifact(uri=stats_path)
    view = Artifact(uri=str(view_path))

    visualise_statistics(statistics, view, other_statistics_path=stats_path)

    assert view_path.exists()
