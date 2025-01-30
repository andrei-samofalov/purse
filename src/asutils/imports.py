import importlib


def ensure_installed(module_name):
    """import helper"""
    try:
        importlib.import_module(module_name)
    except ImportError:
        raise ImportError(f"{module_name} is not installed")
