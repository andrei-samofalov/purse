import importlib


def ensure_installed(*module_names):
    """import helper"""
    errors = []
    for module_name in module_names:
        try:
            importlib.import_module(module_name)
        except ImportError:
            errors.append(ImportError(f"{module_name} is not installed"))

    if errors:
        raise ExceptionGroup("packages not found", errors)
