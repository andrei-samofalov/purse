import logging

from purse._meta import __project__


def logger_factory(name, include_project: bool = False) -> logging.Logger:
    """Logger factory"""
    if include_project:
        return logging.getLogger(f"{__project__}.{name}")
    return logging.getLogger(name)
