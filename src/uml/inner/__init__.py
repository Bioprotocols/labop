# Load the ontology and create a Python module called labop_submodule
import os
import posixpath

from sbol_factory import SBOLFactory

# Load ontology and create uml submodule
SBOLFactory(
    "uml_submodule",
    posixpath.join(os.path.dirname(os.path.realpath(__file__)), "uml.ttl"),
    "http://bioprotocols.org/uml#",
)
# Import symbols into the top-level labop module
from uml_submodule import *
