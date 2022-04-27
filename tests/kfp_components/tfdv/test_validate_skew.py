from kfp.v2.dsl import Artifact
import tensorflow_data_validation as tfdv


def test_validate_skew(tmpdir, make_csv_file):
    """
    Assert that validate_skew produces an anomalies in protobuf text format file.

    Args:
        tmpdir: pytest tmpdir fixture
        make_csv_file: pytest fixture defined in conftest.py

    Returns:
        None
    """

    from pipelines.kfp_components.tfdv import validate_skew

    # prepare paths
    schema_path = "tests/kfp_components/tfdv/assets/validate_schema.pbtxt"
    data_path = str(tmpdir.join("train.csv"))
    train_stats_path = str(tmpdir.join("train.stats"))
    serve_stats_path = str(tmpdir.join("serve.stats"))
    anomalies_path = tmpdir.join("anomalies.pbtxt")

    # populate data
    make_csv_file(1, 100, data_path)

    train_stats = tfdv.generate_statistics_from_csv(data_path)
    tfdv.write_stats_text(train_stats, train_stats_path)

    serve_stats = tfdv.generate_statistics_from_csv(data_path)
    tfdv.write_stats_text(serve_stats, serve_stats_path)

    serve_statistics = Artifact(uri=serve_stats_path)
    anomalies = Artifact(uri=str(anomalies_path))

    validate_skew(
        training_statistics_path=train_stats_path,
        schema_path=schema_path,
        anomalies=anomalies,
        serving_statistics=serve_statistics,
        environment=None,
    )

    assert anomalies_path.exists()
