import json
from typing import List

import autoprotocol

import paml_autoprotocol.plate_coordinates as pc
import tyto
import uml
import paml

from autoprotocol.container import Container, WellGroup, Well
from autoprotocol.instruction import Provision, Spectrophotometry
from autoprotocol.protocol import Protocol
from autoprotocol.unit import Unit
from autoprotocol import container_type as ctype
from paml_autoprotocol.behavior_specialization import BehaviorSpecialization
from paml_autoprotocol.term_resolver import TermResolver
from paml_autoprotocol.transcriptic_api import TranscripticAPI


class UnresolvedTerm():
    def __init__(self, step, attribute, term):
        self.step = step
        self.attribute = attribute
        self.term = term

    def __repr__(self):
        return f"UnresolvedTerm(step={self.step}, attribute=\"{self.attribute}\", term=\"{self.term}\")"

class ResolvedTerm():
    def __init__(self, unresolved_term : UnresolvedTerm, resolution):
        self.unresolved_term = unresolved_term
        self.resolution = resolution

    def resolve(self):
        if isinstance(self.unresolved_term.step, autoprotocol.Container):
            self.unresolved_term.step[self.unresolved_term.attribute] = self.resolution
        elif isinstance(self.unresolved_term.step, autoprotocol.instruction.Instruction):
            self.unresolved_term.step.data[self.unresolved_term.attribute] = self.resolution


class AutoprotocolSpecialization(BehaviorSpecialization):
    def __init__(self, out_path, api: TranscripticAPI = None, resolver : TermResolver = None) -> None:
        super().__init__()
        self.out_path = out_path
        self.resolver = resolver
        self.unresolved_terms = []
        self.api = api
        self.var_to_entity = {}
        self.protocol = Protocol()

    def _init_behavior_func_map(self) -> dict:
        return {
            "https://bioprotocols.org/paml/primitives/sample_arrays/EmptyContainer" : self.define_container,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Provision" : self.provision_container,
            "https://bioprotocols.org/paml/primitives/sample_arrays/PlateCoordinates" : self.plate_coordinates,
            "https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance" : self.measure_absorbance,
        }
    
    def on_begin(self):
        self.protocol = Protocol()

    def on_end(self):
        with open(self.out_path, "w") as f:
            json.dump(self.protocol.as_dict(), f, indent=2)

    def define_container(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        spec = parameter_value_map["specification"]
        samples_var = parameter_value_map["samples"]

        container_spec = {
                "name": samples_var,
                "cont_type": ctype.FLAT96.shortname, # resolve with spec here
                "volume": "1000:microliter", # FIXME where does this come from?
                "properties": [
                    {
                        "key": "concentration",
                        "value": "10:millimolar"
                    }
                ]
            }


        #[container] = self.api.make_containers([container_spec])
        container = self.protocol.ref(samples_var, cont_type=ctype.FLAT96, discard=True)
        self.var_to_entity[samples_var] = container

        #spec_term = UnresolvedTerm(None, samples_var, spec)
        #self.unresolved_terms.append(spec_term)

        return results

    # def provision_container(self, wells: WellGroup, amounts = None, volumes = None, informatics = None) -> Provision:
    def provision_container(self, record: paml.ActivityNodeExecution) -> Provision:
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        destination = parameter_value_map["destination"]
        dest_wells = self.var_to_entity[destination]
        (value, units) = parameter_value_map["amount"]
        units = tyto.OM.get_term_by_uri(units)
        resource = parameter_value_map["resource"]
        print(f"provision_container:")
        print(f" destination: {destination}")
        print(f" amount: {value} {units}")
        print(f" resource: {resource}")
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

        source = parameter_value_map["source"]
        container = self.var_to_entity[source]
        coords = parameter_value_map["coordinates"]
        wells = pc.coordinate_rect_to_well_group(container, coords)

        self.var_to_entity[parameter_value_map['samples']] = wells
        print(f"plate_coordinates:")
        print(f"  source: {source}")
        print(f"  coordinates: {coords}")
        #results[outputs['samples']] = ('samples', pc.coordinate_rect_to_well_group(source, coords))
        return results

    def measure_absorbance(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        wl = parameter_value_map["wavelength"]
        wl_units = tyto.OM.get_term_by_uri(wl.unit)
        samples = parameter_value_map["samples"]
        wells = self.var_to_entity[samples]

        # HACK extract contrainer from well group since we do not have it as input
        container = wells[0].container
        
        print(f"measure_absorbance:")
        print(f"  container: {container}")
        print(f"  samples: {samples}")
        print(f"  wavelength: {wl.value} {wl_units}")

        self.protocol.spectrophotometry(
            dataref="measure_absorbance",
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

    def resolve(self, resolved_terms : List[ResolvedTerm]):
        for term in resolved_terms:
            term.resolve()