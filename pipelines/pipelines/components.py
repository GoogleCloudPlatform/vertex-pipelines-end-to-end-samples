from kfp.components import load_component_from_file
from pathlib import Path

PIPELINE_COMPONENTS_DIR = Path(__file__).parents[2] / "pipeline_components"

# _tensorflow components

train_tensorflow_model = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "_tensorflow"
        / "_tensorflow"
        / "train"
        / "component.yaml"
    )
)

predict_tensorflow_model = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "_tensorflow"
        / "_tensorflow"
        / "predict"
        / "component.yaml"
    )
)

# _tfdv components

generate_statistics = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "_tfdv"
        / "_tfdv"
        / "generate_statistics"
        / "component.yaml"
    )
)

show_anomalies = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "_tfdv"
        / "_tfdv"
        / "show_anomalies"
        / "component.yaml"
    )
)

validate_schema = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "_tfdv"
        / "_tfdv"
        / "validate_schema"
        / "component.yaml"
    )
)

validate_skew = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR / "_tfdv" / "_tfdv" / "validate_skew" / "component.yaml"
    )
)

visualise_statistics = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "_tfdv"
        / "_tfdv"
        / "visualise_statistics"
        / "component.yaml"
    )
)

# _xgboost components

train_xgboost_model = load_component_from_file(
    str(PIPELINE_COMPONENTS_DIR / "_xgboost" / "_xgboost" / "train" / "component.yaml")
)

predict_xgboost_model = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR / "_xgboost" / "_xgboost" / "predict" / "component.yaml"
    )
)

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
        / "upload_model"
        / "component.yaml"
    )
)

# bigquery components

extract_bq_to_dataset = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "bigquery"
        / "bigquery"
        / "extract_dataset"
        / "component.yaml"
    )
)

bq_query_to_table = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "bigquery"
        / "bigquery"
        / "query_to_table"
        / "component.yaml"
    )
)

load_dataset_to_bq = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "bigquery"
        / "bigquery"
        / "upload_prediction"
        / "component.yaml"
    )
)

# evaluation components

compare_models = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "evaluation"
        / "evaluation"
        / "compare_models"
        / "component.yaml"
    )
)

calculate_eval_metrics = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "evaluation"
        / "evaluation"
        / "evaluation_metrics_tfma"
        / "component.yaml"
    )
)

# helpers

copy_artifact = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "helpers"
        / "helpers"
        / "copy_artifact"
        / "component.yaml"
    )
)

model_to_uri = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "helpers"
        / "helpers"
        / "get_model_uri"
        / "component.yaml"
    )
)

quote_csv_header = load_component_from_file(
    str(
        PIPELINE_COMPONENTS_DIR
        / "helpers"
        / "helpers"
        / "quote_csv_header"
        / "component.yaml"
    )
)
