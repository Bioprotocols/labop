from sbol_factory import SBOLFactory, Document, ValidationReport, UMLFactory
import sbol3 as sbol
import os
import posixpath

# Import ontology
__factory__ = SBOLFactory(locals(), 
                          posixpath.join(os.path.dirname(os.path.realpath(__file__)),
                                         'paml.ttl'),
                          'http://bioprotocols.org/paml#')
__umlfactory__ = UMLFactory(__factory__)

