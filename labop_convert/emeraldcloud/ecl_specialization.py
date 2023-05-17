import logging
from typing import Dict

import sbol3
import tyto
import xarray as xr

import labop
import uml
from labop.strings import Strings
from labop_convert.behavior_specialization import (
    BehaviorSpecialization,
    ContO,
    validate_spec_query,
)
from labop_convert.plate_coordinates import flatten_coordinates, get_sample_list

l = logging.getLogger(__file__)
l.setLevel(logging.INFO)


class ECLSpecialization(BehaviorSpecialization):

    # Map terms in the Container ontology to OT2 API names
    LABWARE_MAP = {
        ContO["96 well plate"]: "96-well Polystyrene Flat-Bottom Plate, Clear",
        ContO["2 mL microfuge tube"]: "2mL Tube",
    }

    def __init__(
        self, filename, resolutions: Dict[sbol3.Identified, str] = None
    ) -> None:
        super().__init__()
        self.resolutions = resolutions if resolutions else {}
        self.var_to_entity = {}
        self.script = ""
        self.script_steps = []
        self.markdown = ""
        self.markdown_steps = []
        self.configuration = {}
        if len(filename.split(".")) == 1:
            filename += ".ecl"
        self.filename = filename
        self.sample_format = Strings.XARRAY

        # Needed for using container ontology
        self.container_api_addl_conditions = "(cont:availableAt value <https://sift.net/container-ontology/strateos-catalog#Strateos>)"

    def _init_behavior_func_map(self) -> dict:
        """
        This function redirects processing of each primitive to the functions
        defined below.  Adding additional mappings here is most likely required.
        """
        return {
            "https://bioprotocols.org/labop/primitives/sample_arrays/EmptyContainer": self.define_container,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Provision": self.provision,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Transfer": self.transfer_to,
            "https://bioprotocols.org/labop/primitives/liquid_handling/TransferByMap": self.transfer_by_map,
            "https://bioprotocols.org/labop/primitives/sample_arrays/PlateCoordinates": self.plate_coordinates,
            "https://bioprotocols.org/labop/primitives/spectrophotometry/MeasureAbsorbance": self.measure_absorbance,
            "https://bioprotocols.org/labop/primitives/sample_arrays/EmptyRack": self.define_rack,
            "https://bioprotocols.org/labop/primitives/sample_arrays/LoadContainerInRack": self.load_container_in_rack,
            "https://bioprotocols.org/labop/primitives/sample_arrays/LoadContainerOnInstrument": self.load_container_on_instrument,
            "https://bioprotocols.org/labop/primitives/sample_arrays/LoadRackOnInstrument": self.load_racks,
            "https://bioprotocols.org/labop/primitives/sample_arrays/ConfigureRobot": self.configure_robot,
            "https://bioprotocols.org/labop/primitives/pcr/PCR": self.pcr,
            "https://bioprotocols.org/labop/primitives/liquid_handling/SerialDilution": self.serial_dilution,
        }

    def handle_process_failure(self, record, exception):
        super().handle_process_failure(record, exception)
        self.script_steps.append(f"# Failure processing record: {record.identity}")

    def on_begin(self, ex: labop.ProtocolExecution):

        protocol = self.execution.protocol.lookup()
        self.data = []

    def on_end(self, ex):
        self.script += self._compile_script()
        self.markdown += self._compile_markdown()
        if self.filename:
            with open(self.filename, "w") as f:
                f.write(self.script)
            print(f"Successful execution. Script dumped to {self.filename}.")
        else:
            l.warn(
                "Writing output of specialization to self.data because no filename specified."
            )
            self.data = self.script

    def _compile_script(self):
        script = ""
        for step in self.script_steps:
            script += f"{step}\n"
        return script

    def _compile_markdown(self):
        markdown = self._materials()
        markdown += "\n## Steps\n"
        for i, step in enumerate(self.markdown_steps):
            markdown += str(i + 1) + ". " + step + "\n"
        return markdown

    def _tipracks(self, left, right):
        leftTipID = left["pipette"]
        rightTipID = right["pipette"]
        tipCount = 0
        tipList = ""
        markdown = ""
        for tiprack in left["tipracks"]:
            tiprackID = tiprack["id"]
            tiprackDeck = tiprack["deck"]
            tipList += f"leftTiprack{tipCount},"
            markdown += f"leftTiprack{tipCount} = protocol.load_labware('{tiprackID}', {tiprackDeck})\n"
            tipCount += 1
        markdown += f"left = protocol.load_instrument('{leftTipID}', 'left', tip_rack={tipList[:-1]})\n"
        tipCount = 0
        tipList = ""
        for tiprack in right["tipracks"]:
            tiprackID = tiprack["id"]
            tiprackDeck = tiprack["deck"]
            tipList += f"rightTiprack{tipCount},"
            markdown += f"rightTiprack{tipCount} = protocol.load_labware('{tiprackID}', {tiprackDeck})\n"
            tipCount += 1
        markdown += f"right = protocol.load_instrument('{rightTipID}', 'right', tip_rack={tipList[:-1]})\n"
        # return markdown

    def _materials(self):
        protocol = self.execution.protocol.lookup()

        materials = {
            obj.name: obj
            for obj in protocol.document.objects
            if type(obj) is sbol3.Component
        }
        markdown = "\n\n## Protocol Materials:\n"
        for name, material in materials.items():
            markdown += f"* [{name}]({material.types[0]})\n"

        # Compute container types and quantities
        document_objects = []
        protocol.document.traverse(lambda obj: document_objects.append(obj))
        call_behavior_actions = [
            obj for obj in document_objects if type(obj) is uml.CallBehaviorAction
        ]
        containers = {}
        for cba in call_behavior_actions:
            input_names = [input.name for input in cba.inputs]
            if "specification" in input_names:
                container = cba.input_pin("specification").value.value.lookup()
            elif "rack" in input_names:
                container = cba.input_pin("rack").value.value.lookup()
            elif (
                "container" in input_names
                and type(cba.input_pin("container")) is uml.ValuePin
            ):
                container = cba.input_pin("container").value.value.lookup()
            else:
                continue
            container_type = validate_spec_query(container.queryString)
            container_name = container.name if container.name else "unnamed"
            qty = cba.input_pin("quantity") if "quantity" in input_names else 1

            if container_type not in containers:
                containers[container_type] = {}
            containers[container_type][container_name] = qty

        for container_type, container_name_map in containers.items():
            for container_name, qty in container_name_map.items():
                container_str = ContO.get_term_by_uri(container_type)
                if "TipRack" in container_type:
                    text = f"* {container_str}"
                elif container_name == "unnamed":
                    text = f"* unnamed {container_str}"
                else:
                    text = f"* `{container_name}` ({container_str})"
                if qty > 1:
                    text += f" (x {qty})"
                text += "\n"
                markdown += text

        return markdown

    def _parameter_value_markdown(self, pv: labop.ParameterValue, is_output=False):
        parameter = pv.parameter.lookup().property_value
        value = (
            pv.value.lookup().value
            if isinstance(pv.value, uml.LiteralReference)
            else pv.value.value
        )
        units = (
            tyto.OM.get_term_by_uri(value.unit)
            if isinstance(value, sbol3.om_unit.Measure)
            else None
        )
        value = str(f"{value.value} {units}") if units else str(value)
        if is_output:
            return f"* `{parameter.name}`"
        else:
            return f"* `{parameter.name}` = {value}"

    def define_container(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        spec = parameter_value_map["specification"]["value"]
        samples = parameter_value_map["samples"]["value"]

        name = spec.name if spec.name else spec.display_id

        # SampleArray fields are initialized in primitive_execution.py
        text = f"""{spec.display_id} = LabelContainer[
    Label -> "{name}",
    Container -> Model[Container, Plate, "96-well Polystyrene Flat-Bottom Plate, Clear"]
]"""
        self.script_steps += [text]

    def time_wait(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        value = parameter_value_map["amount"]["value"].value
        units = parameter_value_map["amount"]["value"].unit
        self.script_steps += [f"time.sleep(value)"]

    def provision(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        destination = parameter_value_map["destination"]["value"]
        value = parameter_value_map["amount"]["value"].value
        units = parameter_value_map["amount"]["value"].unit
        units = tyto.OM.get_term_by_uri(units)
        resource = parameter_value_map["resource"]["value"]
        amount = parameter_value_map["amount"]["value"]

    def transfer_to(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):

        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        destination = parameter_value_map["destination"]["value"]
        source = parameter_value_map["source"]["value"]
        if type(source) is labop.SampleMask:
            source = source.source.lookup()
        print(f"Transfer from {source.container_type.lookup().display_id}")
        source = self.resolutions[
            source.container_type.lookup().identity
        ]  # Map to ECL reagent identifier
        amount = ecl_measure(parameter_value_map["amount"]["value"])

        upstream_execution = record.get_token_source(
            parameter_value_map["destination"]["parameter"].property_value
        )
        behavior_type = get_behavior_type(upstream_execution)
        print(behavior_type)

        text = f"""Transfer[
      Source -> Model[Sample, StockSolution, {source}],
      Amount -> {amount},
      Destination -> {ecl_coordinates(destination)}
      ]"""
        self.script_steps += [text]

    def transfer_by_map(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):

        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        destination = parameter_value_map["destination"]["value"]
        source = parameter_value_map["source"]["value"]
        plan = parameter_value_map["plan"]["value"]
        temperature = parameter_value_map["temperature"]["value"]
        value = parameter_value_map["amount"]["value"].value

    def plate_coordinates(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        source = parameter_value_map["source"]["value"]
        coords = parameter_value_map["coordinates"]["value"]
        samples = parameter_value_map["samples"]["value"]
        # samples.mask = coords

    def measure_absorbance(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        wavelength = ecl_measure(parameter_value_map["wavelength"]["value"])
        samples = parameter_value_map["samples"]["value"]

        if type(samples) is labop.SampleMask:
            samples = samples.source.lookup()
        container = samples.container_type.lookup()
        container_name = container.name if container.name else container.display_id

        text = f"""AbsorbanceIntensity[
      Sample -> "{container_name}",
      Wavelength -> {wavelength},
      PlateReaderMix -> True,
      PlateReaderMixRate -> 700 RPM,
      BlankAbsorbance -> False
      ]"""
        self.script_steps += [text]

    def define_rack(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        spec = parameter_value_map["specification"]["value"]
        slots = parameter_value_map["slots"]["value"]

        # FIXME the protocol var_to_entity mapping links variables created in
        # the execution trace with real values assigned here, such as
        # container below.  This mapping can be used in later processing to
        # reuse bindings.
        #
        # self.var_to_entity[samples_var] = container

        # OT2Props = json.loads(spec.OT2SpecificProps)
        # OT2Deck = OT2Props["deck"]

    def load_container_in_rack(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        container: labop.ContainerSpec = parameter_value_map["container"]["value"]
        coords: str = (
            parameter_value_map["coordinates"]["value"]
            if "coordinates" in parameter_value_map
            else "A1"
        )
        slots: labop.SampleCollection = parameter_value_map["slots"]["value"]
        samples: labop.SampleMask = parameter_value_map["samples"]["value"]

    def load_container_on_instrument(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        container_spec: labop.ContainerSpec = parameter_value_map["specification"][
            "value"
        ]
        slots: str = (
            parameter_value_map["slots"]["value"]
            if "slots" in parameter_value_map
            else "A1"
        )
        instrument: sbol3.Agent = parameter_value_map["instrument"]["value"]
        samples: labop.SampleArray = parameter_value_map["samples"]["value"]

    def load_racks(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        node = record.node.lookup()
        parameter_value_map = call.parameter_value_map()
        coords: str = (
            parameter_value_map["coordinates"]["value"]
            if "coordinates" in parameter_value_map
            else "1"
        )
        rack: labop.ContainerSpec = parameter_value_map["rack"]["value"]

        container_types = self.resolve_container_spec(rack)
        selected_container_type = self.check_lims_inventory(container_types)
        if selected_container_type not in LABWARE_MAP:
            raise Exception(
                f"Load failed. {selected_container_type} is not recognized as compatible labware for OT2 machine."
            )

        if coords in self.configuration:
            raise Exception(
                f"Failed to load {rack_str} in Deck {coords}. The Deck is already occupied by {self.configuration[coords]}"
            )
        self.configuration[coords] = rack

        api_name = LABWARE_MAP[selected_container_type]
        self.script_steps += [
            f"labware{coords} = protocol.load_labware('{api_name}', '{coords}')"
        ]
        rack_str = get_container_name(rack)
        self.markdown_steps += [f"Load {rack_str} in Deck {coords} of OT2 instrument"]

        # If the loaded labware is a tiprack, check if any compatible pipettes
        # are currently loaded
        if "TipRack" in rack.queryString:
            select_pipette = None
            for pipette in self.configuration.values():
                if (
                    pipette.display_id in COMPATIBLE_TIPS
                    and api_name in COMPATIBLE_TIPS[pipette.display_id]
                ):
                    select_pipette = pipette.display_id
                    break
            if select_pipette:
                self.script_steps += [
                    f"{select_pipette}.tip_racks.append(labware{coords})"
                ]

    def configure_robot(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        instrument = parameter_value_map["instrument"]["value"]
        mount = parameter_value_map["mount"]["value"]

        allowed_mounts = ["left", "right"]
        allowed_decks = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
        if mount not in allowed_mounts and mount not in allowed_decks:
            raise Exception(
                "ConfigureInstrument call failed: mount must be either 'left' or 'right' or a deck number from 1-12"
            )

        self.configuration[mount] = instrument

        if mount in allowed_mounts:
            self.markdown_steps += [
                f"Mount `{instrument.name}` in {mount} mount of the OT2 instrument"
            ]
            self.script_steps += [
                f"{instrument.display_id} = protocol.load_instrument('{instrument.display_id}', '{mount}')"
            ]
            if instrument.display_id not in COMPATIBLE_TIPS:
                raise Exception(
                    f"ConfigureInstrument call failed: instrument must be one of {list(COMPATIBLE_TIPS.keys())}"
                )

        else:
            self.markdown_steps += [
                f"Mount `{instrument.name}` in Deck {mount} of the OT2 instrument"
            ]
            instrument_id = instrument.display_id.replace(
                "_", " "
            )  # OT2 api name uses spaces instead of underscores
            self.script_steps += [
                f"{instrument.display_id} = protocol.load_module('{instrument_id}', '{mount}')"
            ]
            if instrument.name == "Thermocycler Module":
                self.script_steps += [f"{instrument.display_id}.open_lid()"]

        # Check if a compatible tiprack has been loaded and configure the pipette
        # to use it
        tiprack_selection = None
        for deck, rack in self.configuration.items():
            if type(rack) is not labop.ContainerSpec:
                continue
            container_types = self.resolve_container_spec(rack)
            selected_container_type = self.check_lims_inventory(container_types)
            api_name = LABWARE_MAP[selected_container_type]
            if api_name in COMPATIBLE_TIPS[instrument.display_id]:
                tiprack_selection = rack
                break
        if tiprack_selection:
            self.script_steps += [
                f"{instrument.display_id}.tip_racks.append(labware{deck})"
            ]

    def pcr(
        self, record: labop.ActivityNodeExecution, execution: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        cycles = parameter_value_map["cycles"]["value"]
        annealing_temp = parameter_value_map["annealing_temp"]["value"]
        extension_temp = parameter_value_map["extension_temp"]["value"]
        denaturation_temp = parameter_value_map["denaturation_temp"]["value"]
        annealing_time = parameter_value_map["annealing_time"]["value"]
        extension_time = parameter_value_map["extension_time"]["value"]
        denaturation_time = parameter_value_map["denaturation_time"]["value"]

        self.script_steps += ["thermocycler_module.close_lid()"]
        profile = [
            {
                "temperature": denaturation_temp.value,
                "hold_time_seconds": denaturation_time.value,
            },
            {
                "temperature": annealing_temp.value,
                "hold_time_seconds": annealing_temp.value,
            },
            {
                "temperature": extension_temp.value,
                "hold_time_seconds": extension_time.value,
            },
        ]
        self.script_steps += [f"profile = {profile}"]
        self.script_steps += [
            f"thermocycler_module.execute_profile(steps=profile, repetitions={cycles})"
        ]
        self.script_steps += ["thermocycler_module.set_block_temperature(4)"]

    def get_instrument_deck(self, instrument: sbol3.Agent) -> str:
        for deck, agent in self.configuration.items():
            if agent == instrument:
                return deck
        raise Exception(
            f"{instrument.display_id} is not currently configured for this robot"
        )

    def serial_dilution(
        self, record: labop.ActivityNodeExecution, execution: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]["value"]
        destination = parameter_value_map["destination"]["value"]
        diluent = parameter_value_map["diluent"]["value"]
        amount = ecl_measure(parameter_value_map["amount"]["value"])
        dilution_factor = parameter_value_map["dilution_factor"]["value"]
        series = parameter_value_map["series"]["value"]

        destination_coordinates = ""
        if isinstance(destination, labop.SampleMask):
            destination_coordinates = flatten_coordinates(
                destination.sample_coordinates(
                    sample_format=self.sample_format, as_list=True
                )
            )
            destination = destination.source.lookup()

        # Get destination container type
        destination_container = destination.container_type.lookup()
        container_types = self.resolve_container_spec(destination_container)
        selected_container_type = self.check_lims_inventory(container_types)
        destination_container = ecl_container(selected_container_type)

        sources = destination_coordinates[:-1]
        destinations = destination_coordinates[1:]
        start_well = destination_coordinates[0]
        end_well = destination_coordinates[-1]
        self.script_steps += [f"startWell = {start_well}"]
        self.script_steps += [f"endWell = {end_well}"]
        self.script_steps += [
            f"serialDilutionSourceWells = Flatten[Transpose[AllWells[]]][startWell ;; endWell - 2]];"
        ]
        self.script_steps += [
            f"serialDilutionDestinationWells = Flatten[Transpose[AllWells[]]][startWell + 1 ;; endWell - 1]];"
        ]
        self.script_steps += [
            f"""
serialDilutionTransfers1 = MapThread[
   Transfer[
     Source -> "{destination_container}",
     Destination -> "{destination_container}",
     SourceWell -> #1,
     DestinationWell -> #2,
     Amount -> {amount},
     SlurryTransfer -> True,
     DispenseMix -> True
     ] &,
   {{serialDilutionSourceWells1, serialDilutionDestinationWells1}}];"""
        ]


def ecl_container(container_type: tyto.URI):
    if container_type in ECLSpecialization.LABWARE_MAP:
        return ECLSpecialization.LABWARE_MAP[container_type]
    if container_type in ContO["96 well plate"].get_instances():
        container = ECLSpecialization.LABWARE_MAP[ContO["96 well plate"]]
        return f'Model[Container, Plate, "{container}"]'
    if container_type in ContO["2 mL microfuge tube"].get_instances():
        container = ECLSpecialization.LABWARE_MAP[ContO["2 mL microfuge tube"]]
        return f'Model[Container, Vessel, "{container}"]'
    raise Exception(
        f"Load failed. Container {container_type} is not supported labware."
    )


def ecl_measure(measure: sbol3.Measure):
    text = str(measure.value)
    if measure.unit == tyto.OM.microliter:
        return text + " Microliter"
    elif measure.unit == tyto.OM.nanometer:
        return text + " Nanometer"
    elif measure.unit == tyto.OM.milliliter:
        return text + " Milliliter"
    raise ValueError(tyto.OM.get_term_by_uri(measure.unit) + " is not a supported unit")


def ecl_coordinates(samples: labop.SampleCollection, sample_format=Strings.XARRAY):
    coordinates = flatten_coordinates(
        samples.sample_coordinates(sample_format=sample_format, as_list=True)
    )
    start = coordinates[0]
    end = coordinates[-1]

    # Get destination container type
    if type(samples) is labop.SampleMask:
        samples = samples.source.lookup()
    container = samples.container_type.lookup()
    container_name = container.name if container.name else container.display_id

    return f"""{{#, "{container_name}"}} & /@  Flatten[Transpose[AllWells[]]][[ {start} ;; {end}]];"""


def get_container_name(container: labop.ContainerSpec):
    if container.name:
        return f"`{container.name}`"
    try:
        prefix, local = container.queryString.split(":")
    except:
        raise Exception(f"Container specification {qname} is invalid.")
    return ContO.get_term_by_uri(f"{ContO.uri}#{local}")


def get_behavior_type(ex: labop.CallBehaviorExecution) -> str:
    # Look up the type of Primitive that a CallBehaviorExecution
    # represents.  Strips the namespace out of the Primitive's URI
    # and returns just the local name, e.g., "PlateCoordinates"
    return ex.node.lookup().behavior.split("/")[-1]
