import sys
import os
import posixpath
import argparse
from opil import OPILFactory, UMLFactory, Query

# MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
# DEFAULT_ONTOLOGY = posixpath.join(MODULE_PATH, 'paml.ttl')
# DEFAULT_NS = 'http://bioprotocols.org/paml#'

# parser = argparse.ArgumentParser()
# parser.add_argument(
#     "-i",
#     "--input",
#     help="Input ontology",
#     default=DEFAULT_ONTOLOGY
# )
# parser.add_argument(
#     "-n",
#     "--namespace",
#     help="Ontology namespace",
#     default=DEFAULT_NS
# )
# parser.add_argument(
#     "-d",
#     "--documentation",
#     help="Output directory for UML",
#     default=None
# )
# parser.add_argument(
#     "-v",
#     "--verbose",
#     help="Print data model as it is generated",
#     default=False,
#     action='store_true'
# )

# # Generate a dictionary from the command-line arguments
# args_dict = vars(parser.parse_args())
# if args_dict['input'] and not args_dict['namespace']:
#     raise Exception('If specifying an input ontology, a namespace must also be specified')

# # Import ontology
# default_ontology = posixpath.join(MODULE_PATH, 'paml.ttl')
# opil_factory = OPILFactory(args_dict['input'], args_dict['namespace'], args_dict['verbose'])

# # Generate documentation
# if args_dict['documentation']:
#     OUTPUT_PATH = args_dict['documentation']
#     if not os.path.exists(OUTPUT_PATH):
#         os.mkdir(OUTPUT_PATH)
#     UMLFactory(opil_factory, OUTPUT_PATH)

# print(globals())