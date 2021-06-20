from sbol_factory import SBOLFactory, UMLFactory
import os
import posixpath

# Import ontology
__factory__ = SBOLFactory(locals(),
                          posixpath.join(os.path.dirname(os.path.realpath(__file__)),
                                         'uml.ttl'),
                          'http://bioprotocols.org/uml#')
__umlfactory__ = UMLFactory(__factory__)
