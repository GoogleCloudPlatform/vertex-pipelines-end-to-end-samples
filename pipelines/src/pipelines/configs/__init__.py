from os import environ as env
from importlib import import_module
from types import ModuleType


def load_config(template: str = env.get("config")) -> ModuleType:
    if template is None:
        raise ValueError("Missing environment variable: config")
    return import_module(f"pipelines.configs.{template}")


__all__ = ["load_config"]
