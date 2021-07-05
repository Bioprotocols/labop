import os
import posixpath
from sbol_factory import SBOLFactory, UMLFactory
import sbol3
import uml # Note: looks unused, but is used in SBOLFactory

# Import ontology
__factory__ = SBOLFactory(locals(),
                          posixpath.join(os.path.dirname(os.path.realpath(__file__)), 'paml_time.ttl'),
                          'http://bioprotocols.org/paml-time#')
__umlfactory__ = UMLFactory(__factory__)
