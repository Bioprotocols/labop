import json
import paml_autoprotocol.plate_coordinates as pc
import tyto

from autoprotocol.container import Container, WellGroup
from autoprotocol.instruction import Provision, Spectrophotometry
from autoprotocol.protocol import Protocol
from autoprotocol.unit import Unit
from autoprotocol import container_type as ctype
from paml_autoprotocol.behavior_specialization import BehaviorSpecialization

class AutoprotocolSpecialization(BehaviorSpecialization):
    def __init__(self, out_path) -> None:
        super().__init__()
        self.out_path = out_path

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

    def define_container(self, inputs, outputs):
        results = {}
        spec = inputs["specification"]
        print(f"define_container")
        print(f"  specification: {spec}")
        # TODO use spec to determine container type
        c = self.protocol.ref("test_container", cont_type=ctype.FLAT96, discard=True)
        results[outputs['samples']] = ('samples', c)
        return results

    # def provision_container(self, wells: WellGroup, amounts = None, volumes = None, informatics = None) -> Provision:
    def provision_container(self, inputs, outputs) -> Provision:
        results = {}
        destination = inputs["destination"]
        (value, units) = inputs["amount"]
        units = tyto.OM.get_term_by_uri(units)
        resource = inputs["resource"][0]
        print(f"provision_container:")
        print(f" destination: {destination}")
        print(f" amount: {value} {units}")
        print(f" resource: {resource}")
        self.protocol.provision(
            resource,
            destination,
            amounts=Unit(value, units)
        )
        return results

    def plate_coordinates(self, inputs, outputs) -> WellGroup:
        results = {}
        source = inputs["source"]
        coords = inputs["coordinates"]
        print(f"plate_coordinates:")
        print(f"  source: {source}")
        print(f"  coordinates: {coords}")
        results[outputs['samples']] = ('samples', pc.coordinate_rect_to_well_group(source, coords))
        return results

    def measure_absorbance(self, inputs, outputs):
        results = {}
        (wl_value, wl_units) = inputs["wavelength"]
        wl_units = tyto.OM.get_term_by_uri(wl_units)
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

