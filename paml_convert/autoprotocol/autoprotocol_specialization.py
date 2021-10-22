import json
from typing import Dict

import sbol3
import transcriptic

import paml_convert.autoprotocol.plate_coordinates as pc
import tyto
import paml

from autoprotocol.container import WellGroup
from autoprotocol.instruction import Provision, Spectrophotometry
from autoprotocol.protocol import Protocol
from autoprotocol.unit import Unit
from autoprotocol import container_type as ctype
from paml_convert.behavior_specialization import BehaviorSpecialization
from paml_convert.autoprotocol.strateos_api import StrateosAPI

from container_api.client_api import matching_containers, strateos_id


import logging

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)

class AutoprotocolSpecialization(BehaviorSpecialization):
    def __init__(self, out_path, api: StrateosAPI = None, resolutions: Dict[sbol3.Identified, str] = None) -> None:
        super().__init__()
        self.out_path = out_path
        self.resolutions = resolutions
        self.api = api
        self.var_to_entity = {}
        self.container_api_addl_conditions = "(cont:availableAt value <https://sift.net/container-ontology/strateos-catalog#Strateos>)"


    def _init_behavior_func_map(self) -> dict:
        return {
            "https://bioprotocols.org/paml/primitives/sample_arrays/EmptyContainer" : self.define_container,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Provision" : self.provision_container,
            "https://bioprotocols.org/paml/primitives/sample_arrays/PlateCoordinates" : self.plate_coordinates,
            "https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance" : self.measure_absorbance,
        }
    
    def on_begin(self):
        protocol_name = self.execution.protocol.lookup().name
        self.protocol = Protocol()

    def on_end(self):
        with open(self.out_path, "w") as f:
            json.dump(self.protocol.as_dict(), f, indent=2)

    def define_container(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        spec = parameter_value_map["specification"]['value']
        samples_var = parameter_value_map["samples"]['value']

        if "container_id" in self.resolutions:
            container_id = self.resolutions["container_id"]
        else:
            container_type = self.get_container_type_from_spec(spec)
            container_name = f"{self.execution.protocol.lookup().name} Container {samples_var}"
            container_id = self.create_new_container(container_name, container_type)

        #container_id = tx.inventory("flat test")['results'][1]['id']
        #container_id = "ct1g9q3bndujat5"
        tx = self.api.get_strateos_connection() # Make sure that connection is alive for making the container object
        tx_container = transcriptic.Container(container_id)
        container = self.protocol.ref(samples_var.name, id=tx_container.id, cont_type=tx_container.container_type, discard=True)
        self.var_to_entity[samples_var] = container

        l.debug(f"define_container:")
        l.debug(f" specification: {spec}")
        l.debug(f" samples: {samples_var}")


        #spec_term = UnresolvedTerm(None, samples_var, spec)
        #self.unresolved_terms.append(spec_term)

        return results

    def get_container_type_from_spec(self, spec):
        short_names = [v.shortname
                       for v in [getattr(ctype, x) for x in dir(ctype)]
                       if isinstance(v, ctype.ContainerType)]
        try:
            possible_container_types = self.resolve_container_spec(spec,
                                                                   addl_conditions=self.container_api_addl_conditions)
            possible_short_names = [strateos_id(x) for x in possible_container_types]
            matching_short_names = [x for x in short_names if x in possible_short_names]
            name_map = {
                '96-ubottom-clear-tc': "96-flat",
                '96-flat-clear-clear-tc': "96-flat"
            }
            mapped_names = [name_map[x] for x in matching_short_names]
            return mapped_names[0]
            # return matching_short_names[0] # FIXME need some error handling here

        except Exception as e:
            l.warning(e)
            container_type = "96-flat"
            l.warning(f"Defaulting container to {container_type}")
            return container_type



    def create_new_container(self, name, container_type):
        container_spec = {
                "name": name,
                "cont_type": container_type, # resolve with spec here
                "volume": "100:microliter", # FIXME where does this come from?
                "properties": [
                    {
                        "key": "concentration",
                        "value": "10:millimolar"
                    }
                ]
            }
        container_ids = self.api.make_containers([container_spec])
        container_id = container_ids[name]
        #tx = self.api.get_transcriptic_connection()
        #container_id = tx.inventory("flat test")['results'][1]['id']
        #container_id = "ct1g9q3bndujat5"
        return container_id

    # def provision_container(self, wells: WellGroup, amounts = None, volumes = None, informatics = None) -> Provision:
    def provision_container(self, record: paml.ActivityNodeExecution) -> Provision:
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        destination = parameter_value_map["destination"]["value"]
        dest_wells = self.var_to_entity[destination]
        value = parameter_value_map["amount"]["value"].value
        units = parameter_value_map["amount"]["value"].unit
        units = tyto.OM.get_term_by_uri(units)
        resource = parameter_value_map["resource"]["value"]
        resource = self.resolutions[resource]
        l.debug(f"provision_container:")
        l.debug(f" destination: {destination}")
        l.debug(f" amount: {value} {units}")
        l.debug(f" resource: {resource}")
        [step] = self.protocol.provision(
            resource,
            dest_wells,
            amounts=Unit(value, units)
        )
        #resource_term = UnresolvedTerm(step, "resource_id", resource)
        #self.unresolved_terms.append(resource_term)
        return results

    def plate_coordinates(self, record: paml.ActivityNodeExecution) -> WellGroup:
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]["value"]
        container = self.var_to_entity[source]
        coords = parameter_value_map["coordinates"]["value"]
        wells = pc.coordinate_rect_to_well_group(container, coords)

        self.var_to_entity[parameter_value_map['samples']["value"]] = wells
        l.debug(f"plate_coordinates:")
        l.debug(f"  source: {source}")
        l.debug(f"  coordinates: {coords}")
        #results[outputs['samples']] = ('samples', pc.coordinate_rect_to_well_group(source, coords))
        return results

    def measure_absorbance(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        wl = parameter_value_map["wavelength"]["value"]
        wl_units = tyto.OM.get_term_by_uri(wl.unit)
        samples = parameter_value_map["samples"]["value"]
        wells = self.var_to_entity[samples]
        measurements = parameter_value_map["measurements"]["value"]

        # HACK extract contrainer from well group since we do not have it as input
        container = wells[0].container
        
        l.debug(f"measure_absorbance:")
        l.debug(f"  container: {container}")
        l.debug(f"  samples: {samples}")
        l.debug(f"  wavelength: {wl.value} {wl_units}")

        self.protocol.spectrophotometry(
            dataref=measurements,
            obj=container,
            groups=Spectrophotometry.builders.groups([
                Spectrophotometry.builders.group(
                    "absorbance",
                    Spectrophotometry.builders.absorbance_mode_params(
                        wells=wells,
                        wavelength=Unit(wl.value, wl_units),
                        num_flashes=None,
                        settle_time=None,
                        read_position=None,
                        position_z=None
                    )
                )
            ])
        )
        return results