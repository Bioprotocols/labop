import difflib
import logging

import sbol3

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)


def prepare_document(
    namespace="https://bioprotocols.org/demo/",
) -> sbol3.Document:
    logger.info("Setting up document")
    sbol3.set_namespace(namespace)
    doc = sbol3.Document()
    return doc


def file_diff(comparison_file, temp_name):
    diffs = []
    with open(comparison_file) as file_1:
        file_1_text = file_1.readlines()

    with open(temp_name) as file_2:
        file_2_text = file_2.readlines()

    # Find and print the diff:
    for line in difflib.unified_diff(
        file_1_text,
        file_2_text,
        fromfile=comparison_file,
        tofile=temp_name,
        lineterm="",
    ):
        diffs.append(line)
    return diffs


def get_short_uuid(obj):
    """
    This function generates a 3 digit id for an object that is stable.

    Parameters
    ----------
    obj : object
        object needing an id
    """

    return obj % 1000
