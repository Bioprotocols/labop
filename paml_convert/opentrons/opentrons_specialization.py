import json
from typing import Dict

import sbol3
import tyto
import paml

from paml_convert.behavior_specialization import BehaviorSpecialization

# FIXME if container ontology is needed, then adapt for use here.
# from container_api.client_api import matching_containers, strateos_id


import logging

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)

class OpentronsSpecialization(BehaviorSpecialization):
    def __init__(self, out_path, resolutions: Dict[sbol3.Identified, str] = None) -> None:
        super().__init__()
        self.out_path = out_path
        self.resolutions = resolutions
        self.var_to_entity = {}

        # Needed for using container ontology
        self.container_api_addl_conditions = "(cont:availableAt value <https://sift.net/container-ontology/strateos-catalog#Strateos>)"


    def _init_behavior_func_map(self) -> dict:
        """
        This function redirects processing of each primitive to the functions
        defined below.  Adding additional mappings here is most likely required.
        """
        return {
            "https://bioprotocols.org/paml/primitives/sample_arrays/EmptyContainer" : self.define_container,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Provision" : self.provision_container,
            "https://bioprotocols.org/paml/primitives/sample_arrays/PlateCoordinates" : self.plate_coordinates,
            "https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance" : self.measure_absorbance,
        }

    def on_begin(self):
        protocol_name = self.execution.protocol.lookup().name


    def on_end(self):
        with open(self.out_path, "w") as f:
            json.dump({}, f, indent=2)  # FIXME replace {} with output

    def define_container(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        spec = parameter_value_map["specification"]['value']
        samples_var = parameter_value_map["samples"]['value']

        # FIXME the protocol var_to_entity mapping links variables created in
        # the execution trace with real values assigned here, such as
        # container below.  This mapping can be used in later processing to
        # reuse bindings.
        #
        # self.var_to_entity[samples_var] = container

        l.debug(f"define_container:")
        l.debug(f" specification: {spec}")
        l.debug(f" samples: {samples_var}")

    # def get_container_type_from_spec(self, spec):
    #     """
    #     FIXME: need to remove Strateos depdency using their shortnames

    #     This function will query the container ontology with the query
    #     defined in spec.
    #     """
    #     short_names = [v.shortname
    #                 for v in [getattr(ctype, x) for x in dir(ctype)]
    #                 if isinstance(v, ctype.ContainerType)]
    #     try:
    #         possible_container_types = self.resolve_container_spec(spec,
    #                                                             addl_conditions=self.container_api_addl_conditions)
    #         possible_short_names = [strateos_id(x) for x in possible_container_types]
    #         matching_short_names = [x for x in short_names if x in possible_short_names]
    #         name_map = {
    #             '96-ubottom-clear-tc': "96-flat",
    #             '96-flat-clear-clear-tc': "96-flat"
    #         }
    #         mapped_names = [name_map[x] for x in matching_short_names]
    #         return mapped_names[0]
    #         # return matching_short_names[0] # FIXME need some error handling here

    #     except Exception as e:
    #         l.warning(e)
    #         container_type = "96-flat"
    #         l.warning(f"Defaulting container to {container_type}")
    #         return container_type



    def provision_container(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        destination = parameter_value_map["destination"]["value"]
        value = parameter_value_map["amount"]["value"].value
        units = parameter_value_map["amount"]["value"].unit
        units = tyto.OM.get_term_by_uri(units)
        resource = parameter_value_map["resource"]["value"]
        l.debug(f"provision_container:")
        l.debug(f" destination: {destination}")
        l.debug(f" amount: {value} {units}")
        l.debug(f" resource: {resource}")

    def plate_coordinates(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        source = parameter_value_map["source"]["value"]
        coords = parameter_value_map["coordinates"]["value"]

        l.debug(f"plate_coordinates:")
        l.debug(f"  source: {source}")
        l.debug(f"  coordinates: {coords}")


    def measure_absorbance(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        wl = parameter_value_map["wavelength"]["value"]
        wl_units = tyto.OM.get_term_by_uri(wl.unit)
        samples = parameter_value_map["samples"]["value"]

        l.debug(f"measure_absorbance:")
        l.debug(f"  samples: {samples}")
        l.debug(f"  wavelength: {wl.value} {wl_units}")
