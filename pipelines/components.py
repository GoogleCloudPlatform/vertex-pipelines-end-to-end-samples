from kfp.components import load_component_from_file
from pathlib import Path

PIPELINE_COMPONENTS_DIR = Path(__file__).parents[1] / "pipeline_components"

# aiplatform components

export_model = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "aiplatform"
        / "aiplatform"
        / "export_model"
        / "component.yaml"
    )
)

get_current_time = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "aiplatform"
        / "aiplatform"
        / "get_current_time"
        / "component.yaml"
    )
)

lookup_model = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "aiplatform"
        / "aiplatform"
        / "lookup_model"
        / "component.yaml"
    )
)

upload_model = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "aiplatform"
        / "aiplatform"
        / "export_model"
        / "component.yaml"
    )
)
