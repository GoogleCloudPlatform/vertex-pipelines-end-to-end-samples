from unittest import mock
from kfp.v2.dsl import Model, Metrics, Dataset

import vertex_components
from google.cloud.aiplatform_v1 import ModelEvaluation


import_model_evaluation = vertex_components.import_model_evaluation.python_func


def test_import_model_evaluation(tmpdir):
    with mock.patch(
        "google.cloud.aiplatform_v1.ModelServiceClient"
    ) as mock_service_client, mock.patch(
        "builtins.open",
        mock.mock_open(read_data='{"accuracy": 0.85, "problemType": "classification"}'),
        create=True,
    ) as mock_open, mock.patch(
        "google.protobuf.json_format.ParseDict"
    ) as mock_parse_dict:

        # Mock Artifacts
        mock_model = Model(uri=tmpdir, metadata={"resourceName": ""})
        mock_metrics = Metrics(uri=tmpdir)
        mock_dataset = Dataset(uri=tmpdir)

        # Create an instance of the mocked ModelServiceClient.
        mock_service_client_instance = mock_service_client.return_value
        # When import_model_evaluation is called during the test,
        # it will return a new ModelEvaluation with the specified name.
        mock_service_client_instance.import_model_evaluation.return_value = (
            ModelEvaluation(name="model_evaluation_name")
        )

        # Set the return value for ParseDict to be a mock ModelEvaluation
        mock_parse_dict.return_value = mock.MagicMock(spec=ModelEvaluation)

        # Call the function
        model_evaluation_name = import_model_evaluation(
            model=mock_model,
            metrics=mock_metrics,
            test_dataset=mock_dataset,
            pipeline_job_id="1234",
            project_location="my-location",
            evaluation_name="Imported evaluation",
        )

        # Assert that the import_model_evaluation method of
        # the mocked ModelServiceClient was called
        mock_service_client_instance.import_model_evaluation.assert_called_once_with(
            parent=mock_model.metadata["resourceName"],
            model_evaluation=mock_parse_dict.return_value,
        )

        # Check that open was called with the correct path
        mock_open.assert_called_once_with(mock_metrics.uri)

        # Assert that the return value of the import_model_evaluation
        # function is as expected.
        assert model_evaluation_name[0] == "model_evaluation_name"
