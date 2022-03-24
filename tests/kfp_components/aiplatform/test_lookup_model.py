import google.cloud.aiplatform  # noqa
from kfp.v2.dsl import Model
from unittest import mock
import pytest


def test_lookup_model(tmpdir):
    """
    Assert lookup_model produces expected resource name, and that list method is
    called with the correct arguemnts

    Args:
        tmpdir: built-in pytest tmpdir fixture

    Returns:
        None
    """

    from pipelines.kfp_components.aiplatform import lookup_model

    with mock.patch("google.cloud.aiplatform.Model") as mock_model:

        # Mock attribute and method

        mock_model.resource_name = "my-model-resource-name"
        mock_model.labels = {"model_label": "my_label"}
        mock_model.list.return_value = [mock_model]

        # Invoke the model look up
        found_model_resource_name = lookup_model(
            model_name="my-model",
            model_label="my_label",
            project_location="europe-west4",
            project_id="my-project-id",
            order_models_by="create_time desc",
            fail_on_model_not_found=False,
            model=Model(uri=str(tmpdir)),
        )

        assert found_model_resource_name == "my-model-resource-name"

        # Check the list method was called once with the correct arguments
        mock_model.list.assert_called_once_with(
            filter='labels.model_label="my_label" \
            AND display_name="my-model"',
            order_by="create_time desc",
            location="europe-west4",
            project="my-project-id",
        )


def test_lookup_model_when_no_models(tmpdir):
    """
    Checks that when there are no models and fail_on_model_found = False,
    lookup_model returns an empty string.

    Args:
        tmpdir: built-in pytest tmpdir fixture

    Returns:
        None
    """

    from pipelines.kfp_components.aiplatform import lookup_model

    with mock.patch("google.cloud.aiplatform.Model") as mock_model:
        mock_model.list.return_value = []
        exported_model_resource_name = lookup_model(
            model_name="my-model",
            model_label="my_label",
            project_location="europe-west4",
            project_id="my-project-id",
            order_models_by="create_time desc",
            fail_on_model_not_found=False,
            model=Model(uri=str(tmpdir)),
        )
    print(exported_model_resource_name)
    assert exported_model_resource_name == ""


def test_lookup_model_when_no_models_fail(tmpdir):
    """
    Checks that when there are no models and fail_on_model_found = True,
    lookup_model raises a RuntimeError.

    Args:
        tmpdir: built-in pytest tmpdir fixture

    Returns:
        None
    """

    from pipelines.kfp_components.aiplatform import lookup_model

    with mock.patch("google.cloud.aiplatform.Model") as mock_model:
        mock_model.list.return_value = []

        # Verify that a ValueError is raised
        with pytest.raises(RuntimeError):
            lookup_model(
                model_name="my-model",
                model_label="my_label",
                project_location="europe-west4",
                project_id="my-project-id",
                order_models_by="create_time desc",
                fail_on_model_not_found=True,
                model=Model(uri=str(tmpdir)),
            )
