from unittest import mock

import pytest

import components  # noqa: E402

undeploy_model = components.undeploy_model.python_func

PROJECT = "test-project"
LOCATION = "europe-west2"
ENDPOINT_ID = "456"


def _make_deployed_model(model_id: str):
    dm = mock.MagicMock()
    dm.id = model_id
    return dm


@mock.patch("google.cloud.aiplatform.Endpoint")
@mock.patch("google.cloud.aiplatform.init")
def test_undeploy_all_models(mock_init, mock_endpoint_cls):
    deployed = [_make_deployed_model("m1"), _make_deployed_model("m2")]
    mock_endpoint = mock.MagicMock()
    mock_endpoint.resource_name = (
        f"projects/{PROJECT}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    )
    mock_endpoint.display_name = "my-endpoint"
    mock_endpoint.list_models.return_value = deployed
    mock_endpoint_cls.return_value = mock_endpoint

    undeploy_model(
        project=PROJECT,
        location=LOCATION,
        endpoint_id=ENDPOINT_ID,
        deployed_model_id="",
        delete_endpoint_if_empty=False,
    )

    mock_init.assert_called_once_with(project=PROJECT, location=LOCATION)
    mock_endpoint_cls.assert_called_once_with(
        f"projects/{PROJECT}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    )
    assert mock_endpoint.undeploy.call_count == 2
    mock_endpoint.undeploy.assert_any_call("m1", traffic_split={"m2": 100})
    mock_endpoint.undeploy.assert_any_call("m2")


@mock.patch("google.cloud.aiplatform.Endpoint")
@mock.patch("google.cloud.aiplatform.init")
def test_undeploy_single_model(mock_init, mock_endpoint_cls):
    deployed = [_make_deployed_model("m1"), _make_deployed_model("m2")]
    mock_endpoint = mock.MagicMock()
    mock_endpoint.resource_name = (
        f"projects/{PROJECT}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    )
    mock_endpoint.display_name = "my-endpoint"
    mock_endpoint.list_models.return_value = deployed
    mock_endpoint_cls.return_value = mock_endpoint

    undeploy_model(
        project=PROJECT,
        location=LOCATION,
        endpoint_id=ENDPOINT_ID,
        deployed_model_id="m2",
        delete_endpoint_if_empty=False,
    )

    mock_endpoint.undeploy.assert_called_once_with("m2", traffic_split={"m1": 100})


@mock.patch("google.cloud.aiplatform.Endpoint")
@mock.patch("google.cloud.aiplatform.init")
def test_undeploy_single_model_raises_when_not_found(mock_init, mock_endpoint_cls):
    deployed = [_make_deployed_model("m1")]
    mock_endpoint = mock.MagicMock()
    mock_endpoint.list_models.return_value = deployed
    mock_endpoint_cls.return_value = mock_endpoint

    with pytest.raises(ValueError, match="not found on endpoint"):
        undeploy_model(
            project=PROJECT,
            location=LOCATION,
            endpoint_id=ENDPOINT_ID,
            deployed_model_id="m99",
            delete_endpoint_if_empty=False,
        )


@mock.patch("google.cloud.aiplatform.Endpoint")
@mock.patch("google.cloud.aiplatform.init")
def test_no_models_is_no_op(mock_init, mock_endpoint_cls):
    mock_endpoint = mock.MagicMock()
    mock_endpoint.list_models.return_value = []
    mock_endpoint_cls.return_value = mock_endpoint

    undeploy_model(
        project=PROJECT,
        location=LOCATION,
        endpoint_id=ENDPOINT_ID,
        delete_endpoint_if_empty=False,
    )

    mock_endpoint.undeploy.assert_not_called()


@mock.patch("google.cloud.aiplatform.Endpoint")
@mock.patch("google.cloud.aiplatform.init")
def test_delete_endpoint_if_empty(mock_init, mock_endpoint_cls):
    deployed = [_make_deployed_model("m1")]
    mock_endpoint = mock.MagicMock()
    mock_endpoint.resource_name = (
        f"projects/{PROJECT}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    )
    mock_endpoint.display_name = "my-endpoint"
    mock_endpoint.list_models.return_value = deployed

    empty_endpoint = mock.MagicMock()
    empty_endpoint.list_models.return_value = []
    empty_endpoint.display_name = "my-endpoint"

    mock_endpoint_cls.side_effect = [mock_endpoint, empty_endpoint]

    undeploy_model(
        project=PROJECT,
        location=LOCATION,
        endpoint_id=ENDPOINT_ID,
        delete_endpoint_if_empty=True,
    )

    empty_endpoint.delete.assert_called_once()


@mock.patch("google.cloud.aiplatform.Endpoint")
@mock.patch("google.cloud.aiplatform.init")
def test_delete_endpoint_if_empty_skipped_when_still_has_models(
    mock_init, mock_endpoint_cls
):
    deployed = [_make_deployed_model("m1")]
    mock_endpoint = mock.MagicMock()
    mock_endpoint.list_models.return_value = deployed

    still_has_models = mock.MagicMock()
    still_has_models.list_models.return_value = [_make_deployed_model("m2")]
    still_has_models.display_name = "my-endpoint"

    mock_endpoint_cls.side_effect = [mock_endpoint, still_has_models]

    undeploy_model(
        project=PROJECT,
        location=LOCATION,
        endpoint_id=ENDPOINT_ID,
        deployed_model_id="m1",
        delete_endpoint_if_empty=True,
    )

    still_has_models.delete.assert_not_called()
