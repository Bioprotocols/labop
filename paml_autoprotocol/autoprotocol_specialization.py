import json
from typing import List

import autoprotocol

import paml_autoprotocol.plate_coordinates as pc
import tyto

from autoprotocol.container import Container, WellGroup
from autoprotocol.instruction import Provision, Spectrophotometry
from autoprotocol.protocol import Protocol
from autoprotocol.unit import Unit
from autoprotocol import container_type as ctype
from paml_autoprotocol.behavior_specialization import BehaviorSpecialization
from paml_autoprotocol.term_resolver import TermResolver

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
    def __init__(self, out_path, resolver : TermResolver = None) -> None:
        super().__init__()
        self.out_path = out_path
        self.resolver = resolver
        self.unresolved_terms = []

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

    def define_container(self, node, inputs, outputs):
        results = {}
        spec = inputs["specification"]
        #c = self.protocol.ref("test_container", cont_type=ctype.FLAT96, discard=True)
        samples_var = outputs["samples"].value.lookup()
        results[outputs['samples']] = ('samples', samples_var)

        spec_term = UnresolvedTerm(None, samples_var, spec)
        self.unresolved_terms.append(spec_term)

        return results

    # def provision_container(self, wells: WellGroup, amounts = None, volumes = None, informatics = None) -> Provision:
    def provision_container(self, node, inputs, outputs) -> Provision:
        results = {}
        destination = inputs["destination"]
        (value, units) = inputs["amount"]
        units = tyto.OM.get_term_by_uri(units)
        resource = inputs["resource"][0]
        print(f"provision_container:")
        print(f" destination: {destination}")
        print(f" amount: {value} {units}")
        print(f" resource: {resource}")
        [step] = self.protocol.provision(
            resource,
            destination,
            amounts=Unit(value, units)
        )
        resource_term = UnresolvedTerm(step, "resource_id", resource)
        self.unresolved_terms.append(resource_term)
        return results

    def plate_coordinates(self, node, inputs, outputs) -> WellGroup:
        results = {}
        source = inputs["source"]
        coords = inputs["coordinates"]
        print(f"plate_coordinates:")
        print(f"  source: {source}")
        print(f"  coordinates: {coords}")
        results[outputs['samples']] = ('samples', pc.coordinate_rect_to_well_group(source, coords))
        return results

    def measure_absorbance(self, node, inputs, outputs):
        results = {}
        (wl_value, wl_units) = inputs["wavelength"]
        wl_units = tyto.OM.get_term_by_uri(wl_units) if wl_units else ""
        samples = inputs["samples"]

        # HACK extract contrainer from well group since we do not have it as input
        container = samples[0].container
        
        print(f"measure_absorbance:")
        print(f"  container: {container}")
        print(f"  samples: {samples}")
        print(f"  wavelength: {wl_value} {wl_units}")

        self.protocol.spectrophotometry(
            dataref="measure_absorbance",
            obj=container,
            groups=Spectrophotometry.builders.groups([
                Spectrophotometry.builders.group(
                    "absorbance",
                    Spectrophotometry.builders.absorbance_mode_params(
                        wells=samples,
                        wavelength=Unit(wl_value, wl_units),
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