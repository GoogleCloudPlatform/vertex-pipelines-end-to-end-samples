from pydantic import BaseModel
from typing import Any


class PreprocessingStep(BaseModel):
    encoder: str
    columns: list[str]
    kwargs: dict[str, Any] = {}
    per_column: bool = False


_MODEL_REGISTRY: dict[str, str] = {
    "XGBRegressor": "xgboost.XGBRegressor",
}


class TrainingConfig(BaseModel):

    label: str
    n_estimators: int
    early_stopping_rounds: int
    objective: str
    booster: str
    learning_rate: float
    min_split_loss: float
    max_depth: int
    train_test_split_size: float
    train_valid_split_size: float
    train_test_random_state: int
    train_valid_random_state: int
    preprocessing: list[PreprocessingStep]
    model: str
    use_eval_set: bool = False
    primary_metric: str

    def get_model_class(self) -> type:
        """Return the model class for the configured model name.

        The import is deferred to runtime so this package does not need the
        modelling library as a dependency. Add new entries to _MODEL_REGISTRY
        to support additional model types.
        """
        import importlib

        if self.model not in _MODEL_REGISTRY:
            raise ValueError(
                f"Unknown model '{self.model}'. Must be one of: {list(_MODEL_REGISTRY)}"
            )
        module_path, class_name = _MODEL_REGISTRY[self.model].rsplit(".", 1)
        return getattr(importlib.import_module(module_path), class_name)

    def get_model_params(self) -> dict:
        """Return the parameters used to instantiate the model."""
        return {
            "n_estimators": self.n_estimators,
            "early_stopping_rounds": self.early_stopping_rounds,
            "objective": self.objective,
            "booster": self.booster,
            "learning_rate": self.learning_rate,
            "min_split_loss": self.min_split_loss,
            "max_depth": self.max_depth,
        }

    def get_split_params(self) -> dict:
        """Return train/validation/test split parameters."""
        return {
            "train_test_split": {
                "test_size": self.train_test_split_size,
                "random_state": self.train_test_random_state,
            },
            "train_valid_split": {
                "test_size": self.train_valid_split_size,
                "random_state": self.train_valid_random_state,
            },
        }

    def get_transformers(self, X_train) -> list[tuple]:
        """Build ColumnTransformer tuples from the preprocessing config.

        For per_column steps, one transformer tuple is created per column.
        OrdinalEncoder automatically receives unknown_value set to the number of
        unique categories seen in training data (required for handle_unknown).
        """
        import sklearn.preprocessing as sk_pre  # noqa: PLC0415

        encoder_registry = {
            "StandardScaler": sk_pre.StandardScaler,
            "OrdinalEncoder": sk_pre.OrdinalEncoder,
            "OneHotEncoder": sk_pre.OneHotEncoder,
        }

        col_list = X_train.columns.tolist()
        transformers = []
        for step in self.preprocessing:
            EncoderClass = encoder_registry[step.encoder]
            col_indices = [col_list.index(col) for col in step.columns]
            if step.per_column:
                for col, idx in zip(step.columns, col_indices):
                    kwargs = dict(step.kwargs)
                    if step.encoder == "OrdinalEncoder":
                        kwargs["unknown_value"] = X_train[col].nunique()
                    transformers.append(
                        (f"{step.encoder} for {col}", EncoderClass(**kwargs), [idx])
                    )
            else:
                transformers.append(
                    (step.encoder, EncoderClass(**step.kwargs), col_indices)
                )
        return transformers
