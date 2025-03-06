import importlib
import os
from pathlib import Path


def get_fqn(cls):
    if cls.__module__ == "builtins":
        return cls.__name__

    return f"{cls.__module__}.{cls.__name__}"


def get_reference_from_fqn(fqn: str):
    module_name, class_name = fqn.rsplit(".", 1)
    module = import_module_safely(module_name)
    return getattr(module, class_name)


def get_class_from_fqn_and_params(fqn: str, params: dict):
    cls = get_reference_from_fqn(fqn)
    return cls(**params)


def import_module_safely(module_name: str):
    # Get the project root directory (assuming this file is in pantheon_v2/utils/)
    project_root = Path(__file__).parent.parent.parent

    # Convert module name to path (e.g., 'pantheon_v2.models.user' -> '/path/to/pantheon_v2/models/user.py')
    module_path = Path(module_name.replace(".", os.sep) + ".py")

    # Check if the module exists within the project directory
    full_path = project_root / module_path

    if not full_path.is_file() or not str(full_path).startswith(str(project_root)):
        raise ValueError(f"Module '{module_name}' is not within the project directory")

    return importlib.import_module(module_name)


def get_model_class(model_name: str) -> type:
    """
    Dynamically import and return the model class based on its fully qualified name.

    Args:
        model_name: Fully qualified model name (e.g., 'pantheon_v2.domains.platform.workflows.netflix.models.models.GeneralData')

    Returns:
        The model class
    """
    try:
        module_path, class_name = model_name.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ValueError(f"Could not load model class '{model_name}': {str(e)}")
