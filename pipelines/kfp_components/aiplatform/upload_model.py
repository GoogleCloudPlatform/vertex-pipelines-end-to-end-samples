from kfp.v2.dsl import Input, Model, component
from pipelines.kfp_components.dependencies import PYTHON37, GOOGLE_CLOUD_AIPLATFORM


@component(base_image=PYTHON37, packages_to_install=[GOOGLE_CLOUD_AIPLATFORM])
def upload_model(
    display_name: str,
    serving_container_image_uri: str,
    model: Input[Model],
    project_location: str,
    project_id: str,
    labels: dict,
    description: str = None,
    sync: bool = True,
) -> str:
    """
    Fetch a model given a model name (display name) and export to GCS.

    Args:
        display_name (str): Required. The display name of the Model. The name can
        be up to 128 characters long and can be consist of any UTF-8 characters.
        serving_container_image_uri (str): Required. The URI of the Model serving
            container.
        model (Input[Model]): Model to be uploaded.
        project_location (str): location of the Google Cloud project
        project_id (str): project id of the Google Cloud project
        description (str): The description of the model. Defaults to None.
        labels (dict): Optional. The labels with user-defined metadata to
            organize your Models. Defaults to None.
            Label keys and values can be no longer than 64
            characters (Unicode codepoints), can only
            contain lowercase letters, numeric characters,
            underscores and dashes. International characters
            are allowed.
            See https://goo.gl/xmQnxf for more information
            and examples of labels.
        sync (bool): Upload model synchronously. Defaults to True.

    Returns:
        str: Resource name of the exported model.
    """

    import logging
    from google.cloud.aiplatform import Model

    # uri expects a folder containing the model binaries
    artifact_uri = model.uri.rsplit("/", 1)[0] + "/model"

    logging.info("upload model...")
    model = Model.upload(
        display_name,
        serving_container_image_uri,
        artifact_uri=artifact_uri,
        description=description,
        project=project_id,
        location=project_location,
        labels=labels,
        sync=sync,
    )

    logging.info(f"uploaded model {model}")

    return model.resource_name
