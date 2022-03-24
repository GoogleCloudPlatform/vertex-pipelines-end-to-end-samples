from kfp.v2.dsl import Artifact
import tensorflow_data_validation as tfdv


def test_validate_statistics(tmpdir, make_csv_file):
    """
    Assert that validate_schema produces an anomalies in protobuf text format file.

    Args:
        tmpdir: pytest tmpdir fixture
        make_csv_file: pytest fixture defined in conftest.py

    Returns:
        None
    """
    from pipelines.kfp_components.tfdv import validate_schema

    schema_path = "tests/kfp_components/tfdv/assets/validate_schema.pbtxt"
    data_path = str(tmpdir.join("train.csv"))
    stats_path = str(tmpdir.join("train.stats"))
    anomalies_path = tmpdir.join("anomalies.pbtxt")

    make_csv_file(1, 100, data_path)

    stats = tfdv.generate_statistics_from_csv(data_path)
    tfdv.write_stats_text(stats, stats_path)

    statistics = Artifact(uri=stats_path)
    anomalies = Artifact(uri=str(anomalies_path))

    validate_schema(statistics, anomalies, schema_path)

    assert anomalies_path.exists()
