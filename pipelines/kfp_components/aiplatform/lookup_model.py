from kfp.v2.dsl import component, Output, Model
from pipelines.kfp_components.dependencies import PYTHON37, GOOGLE_CLOUD_AIPLATFORM


@component(base_image=PYTHON37, packages_to_install=[GOOGLE_CLOUD_AIPLATFORM])
def lookup_model(
    model_name: str,
    project_location: str,
    project_id: str,
    model_label: str,
    model: Output[Model],
    order_models_by: str = "create_time desc",
    fail_on_model_not_found: bool = False,
) -> str:
    """
    Fetch a model given a model name (display name) and export to GCS.

    Args:
        model_name (str): display name of the model
        project_location (str): location of the Google Cloud project
        project_id (str): project id of the Google Cloud project
        model (Output[Model]): a Vertex AI model
        order_models_by (str): if multiple models are found based on the display name,
            use a filter clause:
            A comma-separated list of fields to order by, sorted in
            ascending order. Use "desc" after a field name for descending.
            Supported fields: `display_name`, `create_time`, `update_time`
            Defaults to "create_time desc".
        fail_on_model_not_found (bool): if set to True, raise runtime error if
            model is not found

    Returns:
        str: Resource name of the found model. Empty string if model not found.
    """

    import logging
    from google.cloud.aiplatform import Model

    logging.info(f"listing models with display name {model_name}")
    models = Model.list(
        filter=f'labels.model_label="{model_label}" \
            AND display_name="{model_name}"',
        order_by=order_models_by,
        location=project_location,
        project=project_id,
    )

    logging.info(f"found {len(models)} models")

    model_resource_name = ""
    if len(models) == 0:
        model.uri = None
        logging.warning(
            f"No model found with name {model_name}"
            + f"(project: {project_id} location: {project_location})"
        )
        if fail_on_model_not_found:
            raise RuntimeError(f"Failed as model not found")
    else:
        target_model = models[0]
        model_resource_name = target_model.resource_name
        logging.info(f"choosing model by order ({order_models_by})")
        logging.info(f"model display name: {target_model.display_name}")
        logging.info(f"model resource name: {target_model.resource_name}")
        logging.info(f"model uri: {target_model.uri}")
        model.uri = model_resource_name
        model.metadata["resourceName"] = model_resource_name

    return model_resource_name
