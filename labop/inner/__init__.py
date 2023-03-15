# Load the ontology and create a Python module called labop_submodule
import os
import posixpath

from sbol_factory import SBOLFactory

import uml

SBOLFactory(
    "labop_submodule",
    posixpath.join(os.path.dirname(os.path.realpath(__file__)), "labop.ttl"),
    "http://bioprotocols.org/labop#",
)

# Import symbols into the top-level labop module
from labop_submodule import *
