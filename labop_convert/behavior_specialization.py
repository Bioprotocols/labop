import json
import logging
import os
from abc import ABC

import tyto

import labop
import uml
from labop.primitive_execution import input_parameter_map
from labop_convert.behavior_dynamics import SampleProvenanceObserver

l = logging.getLogger(__file__)
l.setLevel(logging.WARN)

container_ontology_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "../labop/container-ontology.ttl",
)
ContO = tyto.Ontology(
    path=container_ontology_path,
    uri="https://sift.net/container-ontology/container-ontology",
)


class BehaviorSpecializationException(Exception):
    pass


class ContainerAPIException(Exception):
    pass


class BehaviorSpecialization(ABC):
    """
    This abstract class defines an API for different conversions from LabOP
    to other formats, such as Markdown or Autoprotocol.
    """

    def __init__(self) -> None:
        super().__init__()
        self._behavior_func_map = self._init_behavior_func_map()
        self.top_protocol = None
        self.execution = None
        self.issues = []
        self.out_dir = None
        self.prov_observer = SampleProvenanceObserver()

        # This data field holds the results of the specialization
        self.data = []

    def initialize_protocol(self, execution: labop.ProtocolExecution, out_dir=None):
        self.execution = execution
        self.out_dir = out_dir

    def _init_behavior_func_map(self) -> dict:
        return {}

    def on_begin(self, execution: labop.ProtocolExecution):
        self.data = []

    def on_end(self, execution: labop.ProtocolExecution):
        try:
            dot_graph = execution.to_dot()
            self.data.append(str(dot_graph.source))
        except Exception as e:
            msg = "Could not render dot graph for execution in DefaultBehaviorSpecialization"
            l.warn(msg)
            self.issues.append(msg)

        self.data = json.dumps(self.data)
        if self.out_dir:
            with open(
                os.path.join(self.out_dir, f"{self.__class__.__name__}.json"),
                "w",
            ) as f:
                f.write(self.data)

    def process(self, record, execution: labop.ProtocolExecution):
        try:
            node = record.node.lookup()
            if not isinstance(node, uml.CallBehaviorAction):
                # raise BehaviorSpecializationException(f"Cannot handle node type: {type(node)}")
                return

            # Subprotocol specializations
            behavior = node.behavior.lookup()
            if isinstance(behavior, labop.Protocol):
                return self._behavior_func_map[behavior.type_uri](record, execution)

            # Individual Primitive specializations
            elif str(node.behavior) not in self._behavior_func_map:
                l.warning(f"Failed to find handler for behavior: {node.behavior}")
                return self.handle(record, execution)
            return self._behavior_func_map[str(node.behavior)](record, execution)
        except Exception as e:
            # l.warn(
            #    f"{self.__class__} Could not process() ActivityNodeException: {record}: {e}"
            # )
            l.warn(
                f"{self.__class__} Could not process {node.behavior.split('#')[-1]}: {e}"
            )

            self.handle_process_failure(record, e)

    def handle_process_failure(self, record, e):
        self.issues.append(e)
        raise e

    def handle(self, record, execution):
        # Save basic information about the execution record
        node = record.node.lookup()
        params = input_parameter_map(
            [
                pv
                for pv in record.call.lookup().parameter_values
                if pv.parameter.lookup().property_value.direction == uml.PARAMETER_IN
            ]
        )
        params = {p: str(v) for p, v in params.items()}
        node_data = {
            "identity": node.identity,
            "behavior": node.behavior,
            "parameters": params,
        }
        self.prov_observer.update(record)
        self.data.append(node_data)

    def resolve_container_spec(self, spec, addl_conditions=None):
        try:
            from container_api import matching_containers

            if "container_api" not in sys.modules:
                raise Exception("Could not import container_api, is it installed?")

            if addl_conditions:
                possible_container_types = matching_containers(
                    spec, addl_conditions=addl_conditions
                )
            else:
                possible_container_types = matching_containers(spec)
        except:
            l.warning("Could not import container_api, is it installed?")
        else:
            try:
                if addl_conditions:
                    possible_container_types = matching_containers(
                        spec, addl_conditions=addl_conditions
                    )
                else:
                    possible_container_types = matching_containers(spec)
                return possible_container_types
            except Exception as e:
                l.warning(e)

        # This fallback only works when the spec query is a simple container class/instance formatted in Manchester owl as cont:<container_uri>. Other container constraints / query criteria are not supported
        l.warning(
            f"Cannot resolve container specification using remote ontology server. Defaulting to static ontology copy"
        )
        container_uri = validate_spec_query(spec.queryString)
        if container_uri.is_instance():
            possible_container_types = [container_uri]
        else:
            possible_container_types = container_uri.get_instances()
        return possible_container_types

    def get_container_typename(self, container_uri: str) -> str:
        # Returns human-readable typename for a container, e.g., '96 well plate'
        return ContO.get_term_by_uri(container_uri)

    def check_lims_inventory(self, matching_containers: list) -> str:
        # Override this method to interface with laboratory lims system
        return matching_containers[0]


class DefaultBehaviorSpecialization(BehaviorSpecialization):
    def _init_behavior_func_map(self) -> dict:
        return {
            "https://bioprotocols.org/labop/primitives/sample_arrays/EmptyContainer": self.handle,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Provision": self.handle,
            "https://bioprotocols.org/labop/primitives/sample_arrays/PlateCoordinates": self.handle,
            "https://bioprotocols.org/labop/primitives/spectrophotometry/MeasureAbsorbance": self.handle,
            "https://bioprotocols.org/labop/primitives/liquid_handling/TransferByMap": self.handle,
            "http://bioprotocols.org/labop#Protocol": self.handle,
        }


def validate_spec_query(query: str) -> "tyto.URI":
    if type(query) is tyto.URI:
        return query

    if "#" in query:
        # Query is assumed to be a URI
        tokens = query.split("#")
        if len(tokens) > 2 or tokens[0] != ContO.uri:
            raise ValueError(
                f"Cannot resolve container specification '{query}'. The query is not a valid URI"
            )
        return tyto.URI(query, ContO)

    # Query is assumed to be a qname
    if ":" in query:
        tokens = query.split(":")
        if (
            len(tokens) > 2 or tokens[0] != "cont"
        ):  # TODO: use prefixMap instead of assuming the prefix is `cont`
            raise ValueError(
                f"Cannot resolve container specification '{query}'. Is the query malformed?"
            )
        return tyto.URI(query.replace("cont:", ContO.uri + "#"), ContO)

    raise ValueError(
        f"Cannot resolve container specification '{query}'. Is the query malformed?"
    )
