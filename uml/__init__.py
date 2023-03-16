import logging

import inspect
import sys
from sbol_factory import SBOLFactory
import sbol3
from sbol3 import PYSBOL3_MISSING


import uml.inner as inner

from .strings import *
from .parameter import *
from .value_specification import *
from .expression import *
from .interval import *
from .duration import *
from .time_expression import *
from .literal_specification import *
from .literal_boolean import *
from .literal_identified import *
from .literal_integer import *
from .literal_null import *
from .literal_real import *
from .literal_reference import *
from .literal_string import *
from .time_interval import *
from .duration_interval import *


from .observation import *
from .duration_observation import *
from .time_observation import *
from .ordered_property_value import *

from .activity_edge import *
from .object_flow import *
from .control_flow import *

from .constraint import *
from .interval_constraint import *
from .time_constraint import *
from .duration_constraint import *


from .executable_node import *
from .action import *
from .invocation_action import *
from .activity_node import *
from .control_node import *
from .object_node import *
from .decision_node import *
from .final_node import *
from .flow_final_node import *
from .fork_node import *
from .initial_node import *
from .activity_parameter_node import *
from .join_node import *
from .merge_node import *

from .activity import *
from .behavior import *
from .call_action import *
from .call_behavior_action import *


from .pin import *
from .input_pin import *
from .output_pin import *
from .value_pin import *


from .uml_graphviz import *

for symbol in dir():
    if isinstance(symbol, sbol3.Identified):
        symbol.__str__ = __str__


def assign_outer_class_builders(module_name):
    outer_classes = inspect.getmembers(sys.modules[module_name])
    inner_class_uris = [
        x for x in SBOLFactory.query.query_classes() if module_name in x
    ]

    for inner_class_uri in inner_class_uris:
        CLASS_NAME = sbol3.utils.parse_class_name(inner_class_uri)
        outer_class = next((cls for (name, cls) in outer_classes if name == CLASS_NAME))
        assign_outer_class_builder(inner_class_uri, outer_class)


def assign_outer_class_builder(inner_class_uri, outer_class):
    arg_names = SBOLFactory.query.query_required_properties(inner_class_uri)
    kwargs = {arg.replace(" ", "_"): PYSBOL3_MISSING for arg in arg_names}

    def builder(identity, type_uri):
        kwargs["identity"] = identity
        kwargs["type_uri"] = type_uri
        return outer_class(**kwargs)

    sbol3.Document.register_builder(str(inner_class_uri), builder)


assign_outer_class_builders(__name__)
