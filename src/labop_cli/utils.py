def project_prefix(project_name: str) -> str:
    try:
        prefix, _ = project_name.rsplit("-")
    except:
        # No -XXX suffix
        prefix = project_name
    return prefix


def project_next_suffix(project_name: str) -> str:
    try:
        prefix, suffix = project_name.rsplit("-")
        next_suffix = str(int(suffix) + 1).zfill(3)
    except:
        # No -XXX suffix
        prefix = project_name
        next_suffix = "001"
    return f"{prefix}-{next_suffix}"


def quick_start_script(project_name: str) -> str:
    return """
import sbol3
from pint import Measurement
from tyto import OM

import labop
"""
