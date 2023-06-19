import json
import logging
import uuid
from typing import Dict

import coordinate_rect_to_row_col_pairs
import sbol3
import transcriptic
import tyto
from autoprotocol import container_type as ctype
from autoprotocol.container import Container, WellGroup
from autoprotocol.instruction import Provision, Spectrophotometry
from autoprotocol.protocol import Protocol
from autoprotocol.unit import Unit
from container_api.client_api import matching_containers, strateos_id

import labop
import labop.utils.plate_coordinates as pc
from labop_convert.autoprotocol.strateos_api import StrateosAPI
from labop_convert.behavior_specialization import BehaviorSpecialization, ContO

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


"""
Autoprotocol specific extensions for Autoprotocol containers
"""


def coordinate_rect_to_well_group(container: Container, coordinates: str):
    indices = coordinate_rect_to_row_col_pairs(coordinates)
    wells = []

    try:
        for i, j in indices:
            well = container.well_from_coordinates(i, j)
            wells.append(well)
        # wells = [container.well_from_coordinates(i, j) for i, j in indices]
    except Exception as e:
        print(container.container_type)
        print(i, j)
        print(container.to_dict())
        raise e
    return WellGroup(wells)


# https://developers.strateos.com/docs/containers
STRATEOS_CONTAINER_TYPES = {
    ContO["96 well PCR plate"]: "96-pcr",
    ContO["96 well plate"]: "96-flat",
    #    "": "96-deep",
    #    "": "96-deep-kf",
    #    "": "96-v-kf",
    #    "": "384-pcr",
    ContO["384 well plate"]: "384-flat",
    #    "": "384-echo",
    ContO["1.5 mL microfuge tube"]: "micro-1.5",
    #    "": "micro-2.0",
}


class AutoprotocolSpecialization(BehaviorSpecialization):
    def __init__(
        self,
        out_path,
        api: StrateosAPI = None,
        resolutions: Dict["sbol3.Identified.identity", str] = None,
    ) -> None:
        super().__init__()
        self.out_path = out_path
        self.resolutions = resolutions if resolutions else {}
        self.api = api
        self.var_to_entity: typing.Dict[
            "labop.SampleArray.identity", autoprotocol.Container
        ] = {}
        self.container_api_addl_conditions = "(cont:availableAt value <https://sift.net/container-ontology/strateos-catalog#Strateos>)"

    def _init_behavior_func_map(self) -> dict:
        return {
            "https://bioprotocols.org/labop/primitives/sample_arrays/EmptyContainer": self.define_container,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Provision": self.provision_container,
            "https://bioprotocols.org/labop/primitives/sample_arrays/PlateCoordinates": self.plate_coordinates,
            "https://bioprotocols.org/labop/primitives/spectrophotometry/MeasureAbsorbance": self.measure_absorbance,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Transfer": self.transfer,
            "https://bioprotocols.org/labop/primitives/liquid_handling/SerialDilution": self.serial_dilution,
            "https://bioprotocols.org/labop/primitives/spectrophotometry/MeasureFluorescence": self.measure_fluorescence,
        }

    def on_begin(self, execution: labop.ProtocolExecution):
        protocol_name = execution.protocol.lookup().name
        self.protocol = Protocol()

    def on_end(self, execution: labop.ProtocolExecution):
        with open(self.out_path, "w") as f:
            json.dump(self.protocol.as_dict(), f, indent=2)

    def define_container(
        self, record: labop.ActivityNodeExecution, execution: labop.ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        spec = parameter_value_map["specification"]["value"]
        samples_var = parameter_value_map["samples"]["value"]

        if "container_id" in self.resolutions:
            container_id = self.resolutions["container_id"]
        elif spec.identity in self.resolutions:
            return
        else:
            container_type = self.get_strateos_container_type(spec)
            container_name = f"{self.execution.protocol.lookup().name} Container {samples_var.display_id}"
            container_id = self.create_new_container(container_name, container_type)
            self.resolutions[spec.identity] = container_id

        # container_id = tx.inventory("flat test")['results'][1]['id']
        # container_id = "ct1g9q3bndujat5"

        tx = (
            self.api.get_strateos_connection()
        )  # Make sure that connection is alive for making the container object
        tx_container = transcriptic.Container(container_id)
        container = self.protocol.ref(
            samples_var.name,
            id=tx_container.id,
            cont_type=tx_container.container_type,
            discard=True,
        )
        self.var_to_entity[samples_var.identity] = container

        l.debug(f"define_container:")
        l.debug(f" specification: {spec}")
        l.debug(f" samples: {samples_var}")

        # spec_term = UnresolvedTerm(None, samples_var, spec)
        # self.unresolved_terms.append(spec_term)

        return results

    def get_container_type_from_spec(self, spec):
        # TODO: Deprecate this.  I could not confirm that it succesfully
        # maps container ontology URIs to Strateos ID.  It also relies
        # on methods in the container API that ought to be encapsulated
        # here in the Autoprotocol specialization.  So I have replaced it
        # with get_strateos_id and STRATEOS_CONTAINER_TYPES
        short_names = [
            v.shortname
            for v in [getattr(ctype, x) for x in dir(ctype)]
            if isinstance(v, ctype.ContainerType)
        ]
        try:
            possible_container_types = self.resolve_container_spec(
                spec, addl_conditions=self.container_api_addl_conditions
            )
            possible_short_names = [strateos_id(x) for x in possible_container_types]
            matching_short_names = [x for x in short_names if x in possible_short_names]
            name_map = {
                "96-ubottom-clear-tc": "96-flat",
                "96-flat-clear-clear-tc": "96-flat",
            }
            mapped_names = [name_map[x] for x in matching_short_names]

        except Exception as e:
            l.warning(e)
            container_type = "96-flat"
            l.warning(f"Defaulting container to {container_type}")
            return container_type

    def get_strateos_container_type(self, spec: labop.ContainerSpec):
        """
        Maps the Container Ontology to Strateos container IDs
        """
        possible_container_types = self.resolve_container_spec(
            spec, addl_conditions=self.container_api_addl_conditions
        )
        container_type = possible_container_types[
            0
        ]  # TODO: what to do if more than one?

        strateos_id = None
        if "StockReagent" in container_type:  # TODO: replace this kludge
            strateos_id = "micro-2.0"
        elif not container_type.is_instance():
            strateos_id = STRATEOS_CONTAINER_TYPES[container_type]
        else:
            # The container map only contains container classes, not
            # instances. Currently tyto does not allow us to look up the
            # class a container instance belongs to, so we have to
            # infer this in the following roundabout way
            for k, v in STRATEOS_CONTAINER_TYPES.items():
                if container_type in k.get_instances():
                    strateos_id = v
                    break
        if not strateos_id:
            raise ValueError(f"No matching Strateos container for {container_type}")
        return strateos_id

    def create_new_container(self, name, container_type):
        container_spec = {
            "name": name,
            "cont_type": container_type,  # resolve with spec here
            "volume": "100:microliter",  # FIXME where does this come from?
            "properties": [{"key": "concentration", "value": "10:millimolar"}],
        }
        # container_spec = {
        #    "name": name,
        #    "cont_type": container_type,  # resolve with spec here
        # }
        container_ids = self.api.make_containers([container_spec])
        container_id = container_ids[name]
        return container_id

    def provision_container(
        self, record: labop.ActivityNodeExecution, execution: labop.ProtocolExecution
    ) -> Provision:
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        destination = parameter_value_map["destination"]["value"]
        value = measure_to_unit(parameter_value_map["amount"]["value"])
        resource = parameter_value_map["resource"]["value"]
        if resource.identity not in self.resolutions:
            raise ValueError(
                f"{resource.identity} does not resolve to a known Strateos id"
            )
        resource = self.resolutions[resource.identity]

        container = self.var_to_entity[destination.identity]
        wells = pc.coordinate_rect_to_well_group(
            container, destination.sample_coordinates()
        )

        [step] = self.protocol.provision(resource, wells, amounts=value)
        # resource_term = UnresolvedTerm(step, "resource_id", resource)
        # self.unresolved_terms.append(resource_term)
        return results

    def plate_coordinates(
        self, record: labop.ActivityNodeExecution, execution: labop.ProtocolExecution
    ) -> WellGroup:

        # TODO: I think this can all be removed because it is now handled in primitive_execution.py
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]["value"]
        samples = parameter_value_map["samples"]["value"]

        container = self.var_to_entity[source.identity]
        self.var_to_entity[samples.identity] = container

    def measure_absorbance(
        self, record: labop.ActivityNodeExecution, execution: labop.ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        wl = parameter_value_map["wavelength"]["value"]
        wl_units = tyto.OM.get_term_by_uri(wl.unit)
        samples = parameter_value_map["samples"]["value"]
        container = self.var_to_entity[samples.identity]
        wells = pc.coordinate_rect_to_well_group(
            container, samples.sample_coordinates()
        )
        measurements = parameter_value_map["measurements"]["value"]

        l.debug(f"measure_absorbance:")
        l.debug(f"  container: {container}")
        l.debug(f"  samples: {samples}")
        l.debug(f"  wavelength: {wl.value} {wl_units}")

        self.protocol.spectrophotometry(
            dataref=str(uuid.uuid5(uuid.NAMESPACE_URL, measurements.identity)),
            obj=container,
            groups=Spectrophotometry.builders.groups(
                [
                    Spectrophotometry.builders.group(
                        "absorbance",
                        Spectrophotometry.builders.absorbance_mode_params(
                            wells=wells,
                            wavelength=Unit(wl.value, wl_units),
                            num_flashes=None,
                            settle_time=None,
                            read_position=None,
                            position_z=None,
                        ),
                    )
                ]
            ),
        )
        return results

    def measure_fluorescence(
        self, record: labop.ActivityNodeExecution, execution: labop.ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        excitation = measure_to_unit(
            parameter_value_map["excitationWavelength"]["value"]
        )
        emission = measure_to_unit(parameter_value_map["emissionWavelength"]["value"])
        bandpass = parameter_value_map["emissionBandpassWidth"]["value"]
        samples = parameter_value_map["samples"]["value"]
        timepoints = (
            parameter_value_map["timepoints"]["value"]
            if "timepoints" in parameter_value_map
            else None
        )
        measurements = parameter_value_map["measurements"]["value"]

        container = self.var_to_entity[samples.identity]
        wells = pc.coordinate_rect_to_well_group(
            container, samples.sample_coordinates()
        )
        self.protocol.spectrophotometry(
            dataref=str(uuid.uuid5(uuid.NAMESPACE_URL, measurements.identity)),
            obj=container,
            groups=Spectrophotometry.builders.groups(
                [
                    Spectrophotometry.builders.group(
                        "fluorescence",
                        Spectrophotometry.builders.fluorescence_mode_params(
                            wells=wells,
                            excitation=[{"ideal": excitation}],
                            emission=[{"ideal": emission}],
                            num_flashes=None,
                            settle_time=None,
                            lag_time=None,
                            integration_time=None,
                            gain=None,
                            read_position=None,
                            position_z=None,
                        ),
                    )
                ]
            ),
        )
        return results

    def transfer(
        self, record: labop.ActivityNodeExecution, execution: labop.ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]["value"]
        destination = parameter_value_map["destination"]["value"]
        destination_coordinates = (
            parameter_value_map["coordinates"]["value"]
            if "coordinates" in parameter_value_map
            else ""
        )
        replicates = (
            parameter_value_map["replicates"]["value"]
            if "replicates" in parameter_value_map
            else 1
        )
        temperature = (
            parameter_value_map["temperature"]["value"]
            if "temperature" in parameter_value_map
            else None
        )
        amount = measure_to_unit(parameter_value_map["amount"]["value"])
        if "dispenseVelocity" in parameter_value_map:
            dispense_velocity = parameter_value_map["dispenseVelocity"]["value"]

        source_container = self.var_to_entity[source.identity]
        source_wells = pc.coordinate_rect_to_well_group(
            source_container, source.sample_coordinates()
        )
        dest_container = self.var_to_entity[destination.identity]
        dest_wells = pc.coordinate_rect_to_well_group(
            dest_container, destination.sample_coordinates()
        )
        self.protocol.transfer(
            source=source_wells, destination=dest_wells, volume=amount
        )

    def serial_dilution(
        self, record: labop.ActivityNodeExecution, execution: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]["value"]
        destination = parameter_value_map["destination"]["value"]
        diluent = parameter_value_map["diluent"]["value"]
        amount = parameter_value_map["amount"]["value"]
        dilution_factor = parameter_value_map["dilution_factor"]["value"]
        xfer_vol = amount.value / dilution_factor
        xfer_vol = Unit(xfer_vol, tyto.OM.get_term_by_uri(amount.unit))
        series = parameter_value_map["series"]["value"]
        container = self.var_to_entity[destination.identity]
        coordinates = destination.get_coordinates()
        if len(coordinates) < 2:
            raise ValueError("Serial dilution must have a series of 2 or more")
        for a, b in zip(coordinates[:-1], coordinates[1:]):
            a_wells = pc.coordinate_rect_to_well_group(container, a)
            b_wells = pc.coordinate_rect_to_well_group(container, b)
            self.protocol.transfer(source=a_wells, destination=b_wells, volume=xfer_vol)


def check_strateos_container_ids():
    """
    This method checks if the current map from Container Ontology to Strateos
    container types is out of date. It could eventually be incorporated into
    regression testing, but is otherwise included here as a developer utility
    """
    shortnames = [
        v.shortname
        for v in [getattr(ctype, x) for x in dir(ctype)]
        if isinstance(v, ctype.ContainerType)
    ]
    unsupported_containers = [
        name for name in shortnames if name not in STRATEOS_CONTAINER_TYPES.values()
    ]
    assert (
        len(unsupported_containers) == 0
    ), f"Found unsupported Strateos container types: {unsupported_containers})"


def measure_to_unit(measure: sbol3.Measure) -> Unit:
    return Unit(measure.value, tyto.OM.get_term_by_uri(measure.unit))
