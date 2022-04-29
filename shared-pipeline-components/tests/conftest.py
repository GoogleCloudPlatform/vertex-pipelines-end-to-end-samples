import numpy as np
import pytest
import pandas as pd
import kfp.v2.dsl


@pytest.fixture(autouse=True)
def patch_kfp_component_decorator(monkeypatch):
    """
    This fixture runs once after all tests are collected.

    Args:
        monkeypatch: Built-in pytest fixture used to patch the decorator `@component`
            in `kfp.v2.dsl`. This prevents KFP from changing the Python functions when
            applying pytests.

    Returns:
        None
    """

    def primitive_decorator(*args, **kwargs):
        """
        A decorator which replaces @component, so that @component will not have any
        effect on any functions.

        Args:
            Accepts any arguments

        Returns:
            func: A decorator which simply returns the input function unchanged.
        """
        return lambda func: func

    # patch the KFP decorator
    monkeypatch.setattr(kfp.v2.dsl, "component", primitive_decorator)


@pytest.fixture(autouse=True)
def mock_kfp_artifact(monkeypatch):
    """
    This fixture runs once after all tests are collected. It mocks the Artifact object
    (and thus any derived classes such as Dataset, Model, etc.) to return the URI as
    the path.

    Unit tests set the URI of artifacts, however, KFP components use Artifact.path to
    retrieve paths to files. If a URI doesn't start with gs:// or minio:// or s3://,
    the path with be None. This behaviour is avoided by mocking the Artifact._get_path
    method.

    Args:
        monkeypatch: Used to patch the decorator `@component` in `kfp.v2.dsl`.
            This prevents KFP from changing the Python functions when applying
            pytests.

    Returns:
        None

    """

    def _get_path(self):
        """
        Returns:
            str: The URI path of the Artifact
        """
        # simply return the URI
        return self.uri

    # mock the _get_path method of Artifact which is used by the property path
    monkeypatch.setattr(kfp.v2.dsl.Artifact, "_get_path", _get_path)


@pytest.fixture(scope="session")
def make_csv_file():
    """
    A factory fixture which can be used in unit tests to make a CSV file

    Args:
        None

    Returns:
        _make_csv_file (function)
    """

    def _make_csv_file(n_features, n_rows, output_path):
        """
        Create CSV file with one label column and N feature columns.

        Args:
            n_features (int): number of features in dataset
            n_rows (int): number of rows in dataset
            output_path (str): destination path to save csv

        Returns:
            None
        """
        columns = ["label"] + [f"feature{x}" for x in range(n_features)]
        df = pd.DataFrame(np.random.rand(n_rows, n_features + 1), columns=columns)
        df.to_csv(output_path, index=False)

    return _make_csv_file
