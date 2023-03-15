import importlib


def inner_to_outer(inner_class):
    # Convert the inner class into an outer class
    labop_module = importlib.import_module("labop")
    labop_class = getattr(labop_module, type(inner_class).__name__)
    return labop_class
