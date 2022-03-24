from kfp.v2.dsl import Model


def test_model_to_uri(tmpdir):
    """
    Test that model_to_uri returns: a uri that has len()>0, the correct model uri.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.helpers import model_to_uri

    model_path = tmpdir.join("/model")

    model = Model(uri=str(model_path))
    parent = False

    model_uri = model_to_uri(model, parent)

    assert len(model_uri) > 0
    assert model_uri == model.uri


def test_model_to_uri_parent(tmpdir):
    """
    Test that model_to_uri returns: a parent uri that has len()>0, the correct parent
    model uri.

    Args:
        tmpdir: pytest tmpdir fixture

    Returns:
        None
    """
    from pipelines.kfp_components.helpers import model_to_uri

    model_path = tmpdir.join("/parent_folder/model")
    model_path_parent = tmpdir.join("/parent_folder")

    model = Model(uri=str(model_path))
    parent = True

    model_uri_parent = model_to_uri(model, parent)

    assert len(model_uri_parent) > 0
    assert model_uri_parent == model_path_parent
