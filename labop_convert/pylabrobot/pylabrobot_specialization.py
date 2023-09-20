import json
import logging
import os
from typing import Dict

import sbol3
import tyto
import xarray as xr

import labop
import uml
from labop.utils.plate_coordinates import get_sample_list
from labop_convert.behavior_specialization import BehaviorSpecialization

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


container_ontology_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "container-ontology.ttl"
)
ContO = tyto.Ontology(
    path=container_ontology_path,
    uri="https://sift.net/container-ontology/container-ontology",
)

# Map pylabrobot pipette names to compatible tipracks
# left is for Pylabrobot names
# right is for LabOp names(container ontology)

# Map terms in the Container ontology of pylabrobot and assign them to LabOP container onthology
# its taking a LabOp term and making a correspondence to a Pylabrobot term
# left is LabOp
# right is container API name on MIcro lab star and starlet (pylabrobot)
# this is for tip carriers, tipracks and 96 well plates of various dimensions

LABWARE_MAP = {
    # this is for TIP carriers (C:\Users\Luiza\pylabrobot\pylabrobot\resources\ml_star\tip_carriers.py)
    # HAMILTON ML star tip carriers
    ContO[
        "ML STAR Tip Carrier with 5 4ml tip with filter racks landscape"
    ]: "TIP_CAR_120BC_4mlTF_A00",
    ContO[
        "ML STAR Tip carrier with 5 5ml tip racks landscape"
    ]: "TIP_CAR_120BC_5mlT_A00",
         ContO["Corning 96 Well Plate"]: "TIP_CAR_288_A00",
    #     ContO["ML STAR Tip carrier for 3 Racks with 96 Tips portrait [revision B00]"]: "TIP_CAR_288_B00",
    #     ContO["ML STAR Tip carrier for 3 Racks with 96 Tips portrait [revision C00]"]: "TIP_CAR_288_C00",
    #     ContO["ML STAR Tip carrier with 3 high volume tip with filter racks portrait [revision A00]"]: "TIP_CAR_288_HTF_A00",
    #     ContO["ML STAR Tip carrier with 3 high volume tip with filter racks portrait [revision B00]"]: "TIP_CAR_288_HTF_B00",
    #     ContO["ML STAR Tip carrier with 3 high volume tip with filter racks portrait [revision C00]"]: "TIP_CAR_288_HTF_C00",
    #     ContO["ML STAR Tip carrier with 3 high volume tip racks portrait [revision A00]"]: "TIP_CAR_288_HT_A00",
    #     ContO["ML STAR Tip carrier with 3 high volume tip racks portrait [revision B00]"]: "TIP_CAR_288_HT_B00",
    #     ContO["ML STAR Tip carrier with 3 high volume tip racks portrait [revision C00]"]: "TIP_CAR_288_HT_C00",
    #     ContO["ML STAR Tip carrier with 3 low volume tip with filter racks portrait [revision A00]"]: "TIP_CAR_288_LTF_A00",
    #     ContO["ML STAR Tip carrier with 3 low volume tip with filter racks portrait [revision B00]"]: "TIP_CAR_288_LTF_B00",
    #     ContO["ML STAR Tip carrier with 3 low volume tip with filter racks portrait [revision C00]"]: "TIP_CAR_288_LTF_C00",
    #     ContO["ML STAR Tip carrier with 3 low volume tip racks portrait [revision A00]"]: "TIP_CAR_288_LT_A00",
    #     ContO["ML STAR Tip carrier with 3 low volume tip racks portrait [revision B00]"]: "TIP_CAR_288_LT_B00",
    #     ContO["ML STAR Tip carrier with 3 low volume tip racks portrait [revision C00]"]: "TIP_CAR_288_LT_C00",
    #     ContO["ML STAR Tip carrier with 3 standard volume tip with filter racks portrait [revision A00]"]: "TIP_CAR_288_STF_A00",
    #     ContO["ML STAR Tip carrier with 3 standard volume tip with filter racks portrait [revision B00]"]: "TIP_CAR_288_STF_B00",
    #     ContO["ML STAR Tip carrier with 3 standard volume tip with filter racks portrait [revision C00]"]: "TIP_CAR_288_STF_C00",
    #     ContO["ML STAR Tip carrier with 3 standard volume tip racks portrait [revision A00]"]: "TIP_CAR_288_ST_A00",
    #     ContO["ML STAR Tip carrier with 3 standard volume tip racks portrait [revision B00]"]: "TIP_CAR_288_ST_B00",
    #     ContO["ML STAR Tip carrier with 3 standard volume tip racks portrait [revision C00]"]: " TIP_CAR_288_ST_C00",
    #     ContO["ML STAR Tip carrier with 3 50ul tip with filter racks portrait [revision C00]"]: "TIP_CAR_288_TIP_50ulF_C00",
    #     ContO["ML STAR Tip carrier with 3 50ul tip racks portrait [revision C00]"]: "TIP_CAR_288_TIP_50ul_C00",
    #     ContO["ML STAR Tip carrier with 4 empty tip rack positions landscape, with Barcode Identification [revision A00]"]: "TIP_CAR_384BC_A00",
    #     ContO["ML STAR Tip carrier with 4 high volume tip with filter racks for 12/16 channel instruments"]: "TIP_CAR_384BC_HTF_A00",
    #     ContO["ML STAR Tip carrier with 4 high volume tip racks for 12/16 channel instruments"]: "TIP_CAR_384BC_HT_A00",
    #     ContO["ML STAR Tip carrier with 4 low volume tip with filter racks for 12/16 channel instruments"]: "TIP_CAR_384BC_LTF_A00",
    #     ContO["ML STAR Tip carrier with 4 low volume tip racks for 12/16 channel instruments"]: "TIP_CAR_384BC_LT_A00",
    #     ContO["ML STAR Tip carrier with 4 standard volume tip with filter racks for 12/16 channel instruments"]: "TIP_CAR_384BC_STF_A00",
    #     ContO["ML STAR Tip carrier with 4 standard volume tip with filter racks for 12/16 channel instruments"]: "TIP_CAR_384BC_ST_A00",
    #     ContO["ML STAR Tip carrier with 4 50ul tip with filter racks landscape [revision A00]"]: "TIP_CAR_384BC_TIP_50ulF_A00",
    #     ContO["ML STAR Tip carrier with 4 50ul tip racks landscape [revision A00]"]: "TIP_CAR_384BC_TIP_50ul_A00",
    #     ContO["ML STAR TIP Carrier for 4 Racks with 96 Tips landscape [revision A00]"]: "TIP_CAR_384_A00",
    #     ContO["ML STAR Tip carrier with 4 high volume tip racks for 12/16 channel instruments, no barcode identification"]: "TIP_CAR_384_HT_A00",
    #     ContO["ML STAR Tip carrier with 4 low volume tip with filter racks for 12/16 channel instruments, no barcode identification"]: "TIP_CAR_384_LTF_A00",
    #     ContO["ML STAR Tip carrier with 4 low volume tip racks for 12/16 channel instruments, no barcode identification"]: "TIP_CAR_384_LT_A00",
    #     ContO["ML STAR Tip carrier with 4 standard volume tip with filter racks for 12/16 channel instruments, no barcode identification  [revision A00] "]: "TIP_CAR_384_STF_A00",
    #     ContO["ML STAR Tip carrier with 4 standard volume tip racks for 12/16 channel instruments, no barcode identification  [revision A00]"]: "TIP_CAR_384_ST_A00",
    #     ContO["ML STAR Tip carrier with 4 50ul tip with filter racks landscape [revision A00]"]: "TIP_CAR_384_TIP_50ulF_A00",
    #     ContO["ML STAR Tip carrier with 4 50ul tip racks landscape [revision A00]"]: "TIP_CAR_384_TIP_50ul_A00",
    #     ContO["ML STAR Tip Carrier for 5 Racks with 96 Tips landscape [revision A00]"]: "TIP_CAR_480",
    #     ContO["NEST 96 Well Plate"]: "nest_96_wellplate_200ul_flat",
    # #this is for PLATES (C:\Users\Luiza\pylabrobot\pylabrobot\resources\corning_costar\plates.py)
    # #"""" Corning Costar plates """
    #     ContO["Corning Costar 10 ul plate [1536]"]: "Cos_1536_10ul",
    #     ContO["Corning Costar deep well plate [384]"]: "Cos_384_DW",
    #     ContO["Corning Costar PCR plate [384]"]: "Cos_384_PCR",
         ContO["Corning Costar 1 mL deep well plate with 96 wells"]: "Cos_96_DW_1mL",
    #     ContO["Corning Costar 2 mL deep well plate [96]"]: "Cos_96_DW_2mL",
    #     ContO["Corning Costar 500ul deep well plate [96]"]: "Cos_96_DW_500ul",
         ContO["Corning Costar EZwash plate with 96 wells"]: "Cos_96_EZWash",
         ContO["Corning 96 Well Plate 360 uL Flat"]: "Cos_96_FL",
         ContO["Corning Costar filter plate with 96 wells"]: "Cos_96_Filter",
    #     ContO["Corning Costar Half area plate [96]"]: "Cos_96_HalfArea",
    #     ContO["Corning Costar filter plate [96]"]: "Cos_96_Filter",
    #     ContO["Corning Costar PCR plate [96]"]: "Cos_96_PCR",
    #     ContO["Corning Costar ProtCryst plate [96]"]: "Cos_96_ProtCryst",
    #     ContO["Corning Costar SpecOps plate [96]"]: "Cos_96_SpecOps",
    #     ContO["Corning Costar RD plate [96]"]: "Cos_96_Rd",
    #     ContO["Corning Costar UV plate [96]"]: "Cos_96_UV",
    #     ContO["Corning Costar Vb plate [96]"]: "Cos_96_Vb",
    # #this is for TIPRACKS (C:\Users\Luiza\pylabrobot\pylabrobot\resources\corning_costar\plates.py)
    # #""" HAMILTON ML Star tips """
    #     ContO["Tip Rack 24x 4ml Tip with Filter landscape oriented"]: "FourmlTF_L",
    #     ContO["Tip Rack 24x 5ml Tip landscape oriented"]: "FivemlT_L",
         ContO["ML STAR Tip Rack with 96 1000ul High Volume Tip with filter"]: "HTF_L",
    #     ContO["Tip Rack with 96 1000ul High Volume Tip"]: "HT_L",
    #     ContO["Tip Rack with 96 10ul Low Volume Tip with filter"]: "LTF_L",
    #     ContO["Tip Rack with 96 10ul Low Volume Tip"]: "LT_L",
    #     ContO["Tip Rack with 96 300ul Standard Volume Tip with filter"]: "STF_L",
    #     ContO["Tip Rack with 96 300ul Standard Volume Tip"]: "ST_L",
    # #this is for Plate carriers (C:\Users\Luiza\pylabrobot\pylabrobot\resources\corning_costar\plates.py)
    # #""" Hamilton ML Star plate carriers """
    #     ContO["Plate Carrier for 5 deep well 96 Well PCR Plates"]: "PLT_CAR_L5AC_A00",
    #     ContO["Plate Carrier for 5 plates"]: "PLT_CAR_L5AC",
    #     ContO["Plate Carrier with 5 adjustable (height) portrait positions for archive plates"]: "PLT_CAR_L5FLEX_AC",
    #     ContO["Plate Carrier with 5 adjustable (height) positions for MTP"]: "PLT_CAR_L5FLEX_MD",
    #     ContO["Plate Carrier with 5 adjustable (height) positions for MTP "]: "PLT_CAR_L5FLEX_MD_A00",
    #     ContO["Plate Carrier for 5 plates"]: "PLT_CAR_L5MD",
    #     ContO["Plate Carrier for 5 96/384-Well Plates"]: "PLT_CAR_L5MD_A00",
    #     ContO["Plate Carrier for 5 PCR plates"]: "PLT_CAR_L5PCR",
    #     ContO["Plate Carrier for 5 PCR landscape plates [revision 00]"]: "PLT_CAR_L5PCR_A00",
    #     ContO["Plate Carrier for 5 PCR landscape plates [revision 01]"]: "PLT_CAR_L5PCR_A01",
    #     ContO["Plate Carrier for 3 96 Deep Well Plates (portrait)"]: "PLT_CAR_P3AC_A00",
    #     ContO["Plate Carrier for 3 96 Deep Well Plates (portrait) [revision 01]"]: "PLT_CAR_P3AC_A01",
    #     ContO["Plate Carrier PLT_CAR_P3HD"]: "PLT_CAR_P3HD",
    #     ContO["Plate Carrier PLT_CAR_P3MD"]: "PLT_CAR_P3MD",
    #     ContO["Plate Carrier for 3 96/384-Well Plates (Portrait)"]: "PLT_CAR_P3MD_A00",
    #     ContO["Plate Carrier PLT_CAR_P3MD"]: "PLT_CAR_P3MD_A01",
    #     ContO["Carrier for 3 96/384-Well Plates (Portrait)"]: "PLT_CAR_P3MD",
    #     ContO["Plate Carrier PLT_CAR_P3MD"]: "PLT_CAR_P3MD_A01",
}

REVERSE_LABWARE_MAP = LABWARE_MAP.__class__(map(reversed, LABWARE_MAP.items()))


class PylabrobotSpecialization(BehaviorSpecialization):
    def __init__(
        self, filename, resolutions: Dict[sbol3.Identified, str] = None
    ) -> None:
        super().__init__()
        self.resolutions = resolutions
        self.var_to_entity = {}
        self.script = ""
        self.script_steps = []
        self.markdown = ""
        self.markdown_steps = []
        self.apilevel = "2.11"
        self.configuration = {}
        self.filename = filename
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
            # "https://bioprotocols.org/labop/primitives/spectrophotometry/MeasureAbsorbance": self.measure_absorbance,
            "https://bioprotocols.org/labop/primitives/sample_arrays/EmptyRack": self.define_rack,
            "https://bioprotocols.org/labop/primitives/sample_arrays/LoadContainerInRack": self.load_container_in_rack,
            "https://bioprotocols.org/labop/primitives/sample_arrays/LoadContainerOnInstrument": self.load_container_on_instrument,
            # "https://bioprotocols.org/labop/primitives/sample_arrays/LoadRackOnInstrument": self.load_racks,
            #"https://bioprotocols.org/labop/primitives/sample_arrays/ConfigureRobot": self.configure_robot,
            #"https://bioprotocols.org/labop/primitives/pcr/PCR": self.pcr,
            "https://bioprotocols.org/labop/primitives/plate_handling/Filter": self.activate_airpump,
        }

        #the protocol should have the namespace 
#    def _materials(self):
 #       protocol = self.execution.protocol.lookup()

#        materials = {
#            obj.name: obj
#            for obj in protocol.document.objects
#            if type(obj) is sbol3.Component
#        }
#        markdown = "\n\n## Protocol Materials:\n"
#        for name, material in materials.items():
#            markdown += f"* [{name}]({material.types[0]})\n"

        # Compute container types and quantities
#        document_objects = []
#        protocol.document.traverse(lambda obj: document_objects.append(obj))
#        call_behavior_actions = [
#            obj for obj in document_objects if type(obj) is uml.CallBehaviorAction
#        ]
#        containers = {}
#        for cba in call_behavior_actions:
#            input_names = [input.name for input in cba.inputs]
#            if "specification" in input_names:
#                container = cba.input_pin("specification").value.value.lookup()
#            elif "rack" in input_names:
#                container = cba.input_pin("rack").value.value.lookup()
#            elif (
#                "container" in input_names
#                and type(cba.input_pin("container")) is uml.ValuePin
#            ):
#                container = cba.input_pin("container").value.value.lookup()
 #           else:
#                continue
#            container_type = container.queryString
##            container_name = container.name if container.name else "unnamed"
 #           qty = cba.input_pin("quantity") if "quantity" in input_names else 1

 #           if container_type not in containers:
 #               containers[container_type] = {}
 #           containers[container_type][container_name] = qty

 #       for container_type, container_name_map in containers.items():
 #           for container_name, qty in container_name_map.items():
 #               container_str = ContO.get_term_by_uri(container_type)
#                if "TipRack" in container_type:
#                    text = f"* {container_str}"
#                elif container_name == "unnamed":
#                    text = f"* unnamed {container_str}"
#                else:
#                    text = f"* `{container_name}` ({container_str})"
#                if qty > 1:
#                    text += f" (x {qty})"
#                text += "\n"
#                markdown += text

    def handle_process_failure(self, record, exception):
        super().handle_process_failure(record, exception)
        self.script_steps.append(f"# Failure processing record: {record.identity}")

    def on_begin(self, ex: labop.ProtocolExecution):
        protocol = self.execution.protocol.lookup()
        apilevel = self.apilevel
        self.markdown += f"# {protocol.name}\n"
        self.script += (
           """import asyncio

from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends.simulation.simulator_backend import (
    SimulatorBackend,
)
from pylabrobot.resources import Cos_96_EZWash, Cos_96_PCR, HTF_L, Coordinate
from pylabrobot.resources.hamilton import STARLetDeck
from pylabrobot import MPE
from pylabrobot import mpebackend


backend = SimulatorBackend()
deck = STARLetDeck()
sb = SimulatorBackend(open_browser=False)
lh = LiquidHandler(backend=sb, deck=STARLetDeck())


async def LiquidHandler_setup():
    await lh.setup()
"""
        )
        self.data = []

    def on_end(self, ex):
        self.script += self._compile_script()
        self.markdown += self._compile_markdown()
        if self.filename:
            with open(self.filename + ".py", "w") as f:
                f.write(self.script)
            with open(self.filename + ".md", "w") as f:
                f.write(self.markdown)
            print(f"Successful execution. Script dumped to {self.filename}.")
        else:
            l.warn(
                "Writing output of specialization to self.data because no filename specified."
            )
            self.data = f"# pylabbot Script\n ```python\n{self.script}```\n # Operator Script\n {self.markdown}"

    def _compile_script(self):
        script = ""
        for step in self.script_steps:
            script += f"    {step}\n"
        return script

    def _compile_markdown(self):
        markdown = self._materials()
        markdown += "\n## Steps\n"
        for i, step in enumerate(self.markdown_steps):
            markdown += str(i + 1) + ". " + step + "\n"
        return markdown

    ###################################################
    # see about def _tipracks object
    ##################################################
    #def _materials(self):
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
            container_type = container.queryString
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
        # SampleArray fields are initialized in primitive_execution.py

    def time_wait(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        value = parameter_value_map["amount"]["value"].value
        units = parameter_value_map["amount"]["value"].unit
        self.script_steps += [f"time.sleep(value)"]

    def plate_coordinates(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        source = parameter_value_map["source"]["value"]
        coords = parameter_value_map["coordinates"]["value"]
        samples = parameter_value_map["samples"]["value"]
        if not hasattr(samples, "mask") or samples.mask is None:
            samples.mask = coords

    # write correspondence for provision primitive
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
        amount = measurement_to_text(amount)
        coords = ""
        coords = (
            destination.get_parent()
            .get_parent()
            .token_source.lookup()
            .node.lookup()
            .input_pin("coordinates")
            .value.value
        )
        upstream_execution = get_token_source("destination", record)
        container = upstream_execution.call.lookup().parameter_value_map()["container"][
            "value"
        ]

        behavior_type = get_behavior_type(upstream_execution)
        if behavior_type == "LoadContainerInRack":
            coords = upstream_execution.call.lookup().parameter_value_map()[
                "coordinates"
            ]["value"]
            upstream_execution = get_token_source("slots", upstream_execution)
            rack = upstream_execution.call.lookup().parameter_value_map()[
                "specification"
            ]["value"]
        else:
            raise NotImplementedError(
                f'A "Provision" call cannot follow a "{behavior_type}" call'
            )

        container_str = (
            f"`{container.name}`" if container.name else container.queryString
        )
        rack_str = f"`{rack.name}`" if rack.name else rack.queryString
        text = f"Fill {amount} of {resource.name} into {container_str} located in {coords} of {rack_str}"
        self.markdown_steps += [text]
        #write pylabrobot correspondence
    # write correspondence for transfer primitive
    def transfer_to(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        destination = parameter_value_map["destination"]["value"]
        source = parameter_value_map["source"]["value"]
        value = parameter_value_map["amount"]["value"].value
        units = parameter_value_map["amount"]["value"].unit
        units = tyto.OM.get_term_by_uri(units)
        OT2Pipette = "left"

        # Trace the "source" pin back to the EmptyContainer to retrieve the
        # ContainerSpec for the destination container
        upstream_execution = record.get_token_source(
            parameter_value_map["source"]["parameter"].property_value
        )
        behavior_type = get_behavior_type(upstream_execution)
        if behavior_type == "PlateCoordinates":
            upstream_map = upstream_execution.call.lookup().parameter_value_map()
            coordinates = upstream_map["coordinates"]["value"]
            upstream_execution = upstream_execution.get_token_source(
                upstream_map["source"]["parameter"].property_value
            )  # EmptyContainer
            parameter_value_map = upstream_execution.call.lookup().parameter_value_map()
            source_container = parameter_value_map["specification"]["value"]
        elif behavior_type == "LoadContainerInRack":
            upstream_execution = upstream_execution.get_token_source(
                upstream_map["slots"]["parameter"].property_value
            )  # EmptyRack
            parameter_value_map = upstream_execution.call.lookup().parameter_value_map()
            source_container = parameter_value_map["specification"]["value"]
        elif behavior_type == "LoadContainerOnInstrument":
            upstream_map = upstream_execution.call.lookup().parameter_value_map()
            coordinates = upstream_map["slots"]["value"]
            upstream_execution = upstream_execution.get_token_source(
                upstream_map["container"]["parameter"].property_value
            )  # EmptyContainer
            parameter_value_map = upstream_execution.call.lookup().parameter_value_map()
            source_container = parameter_value_map["specification"]["value"]

        else:
            raise Exception(f'Invalid input pin "source" for Transfer.')

        # Map the source container to a variable name in the pylabrobot api script
        source_name = None
        for deck, labware in self.configuration.items():
            if labware == source_container:
                source_name = f"labware{deck}"
                break
        if not source_name:
            raise Exception(f"{source_container} is not loaded.")

        # Trace the "destination" pin back to the EmptyContainer execution
        # to retrieve the ContainerSpec for the destination container
        parameter_value_map = call.parameter_value_map()
        upstream_execution = record.get_token_source(
            parameter_value_map["destination"]["parameter"].property_value
        )
        behavior_type = get_behavior_type(upstream_execution)
        if behavior_type == "PlateCoordinates":
            upstream_map = upstream_execution.call.lookup().parameter_value_map()
            coordinates = upstream_map["coordinates"]["value"]
            upstream_execution = upstream_execution.get_token_source(
                upstream_map["source"]["parameter"].property_value
            )  # EmptyContainer
            parameter_value_map = upstream_execution.call.lookup().parameter_value_map()
            destination_container = parameter_value_map["specification"]["value"]

        elif behavior_type == "LoadContainerOnInstrument":
            upstream_map = upstream_execution.call.lookup().parameter_value_map()
            coordinates = upstream_map["slots"]["value"]
            upstream_execution = upstream_execution.get_token_source(
                upstream_map["container"]["parameter"].property_value
            )  # EmptyContainer
            parameter_value_map = upstream_execution.call.lookup().parameter_value_map()
            destination_container = parameter_value_map["specification"]["value"]

        else:
            raise Exception(f'Invalid input pin "destination" for Transfer.')
        destination_name = None
        for deck, labware in self.configuration.items():
            if type(labware) is sbol3.Agent and hasattr(labware, "configuration"):
                # If labware is a hardware module (i.e. Agent),
                # then we need to look further to find out what conta
                coordinate = get_sample_list(destination.mask)[0]
                if coordinate in labware.configuration:
                    labware = labware.configuration[coordinate]
            if labware == destination_container:
                destination_name = f"labware{deck}"
                break
        if not destination_name:
            raise Exception(f"{destination_container} is not loaded.")

        # TODO: automatically choose pipette based on transferred volume
        if not self.configuration:
            raise Exception(
                "Transfer call failed. Use ConfigureInstrument to configure a pipette"
            )
        pipette = self.configuration["left"]

        comment = record.node.lookup().name
        comment = (
            "# " + comment
            if comment
            else "# Transfer ActivityNode name is not defined."
        )

        source_str = source.mask
        destination_str = destination.mask
        for c_source in source.get_coordinates():
            for c_destination in destination.get_coordinates():
                self.script_steps += [ # make it a list with 5 elements (pick up, aspirate, dispense, return tips)
                    f"{pipette.display_id}.transfer({value}, {source_name}['{c_source}'], {destination_name}['{c_destination}'])  {comment}"
                ]

    # write correspondence for transferbymap primitive
    def transfer_by_map(
        self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        destination = parameter_value_map["destination"]["value"] #those are gonna be sample arrays
        source = parameter_value_map["source"]["value"]#those are gonna be sample arrays
        plan = parameter_value_map["plan"]["value"]
        temperature = parameter_value_map["temperature"]["value"]
        value = parameter_value_map["amount"]["value"].value
        units = parameter_value_map["amount"]["value"].unit
        units = tyto.OM.get_term_by_uri(units)
        pylabrobot = "left"

        # Trace the "source" pin back to the EmptyContainer to retrieve the
        # ContainerSpec for the destination container
        upstream_execution = record.get_token_source("source")
        behavior_type = get_behavior_type(upstream_execution)
        if behavior_type == "LoadContainerInRack":
            upstream_execution = upstream_execution.get_token_source(
                "slots"
            )  # EmptyRack
            parameter_value_map = upstream_execution.call.lookup().parameter_value_map()
            source_container = parameter_value_map["specification"]["value"]
        else:
            raise Exception(f'Invalid input pin "source" for Transfer.')

        #############trace the source container to a variable name in the pylabrobot script######## 
        source_name = None
        for deck, labware in self.configuration.items():
            if labware == source_container:
                source_name = f"labware{deck}"
                break
        if not source_name:
            raise Exception(f"{source_container} is not loaded.")

        # Trace the "destination" pin back to the EmptyContainer execution
        # to retrieve the ContainerSpec for the destination container
        upstream_execution = record.get_token_source("destination")
        behavior_type = get_behavior_type(upstream_execution)
        if behavior_type == "PlateCoordinates":
            upstream_execution = get_token_source(
                "source", upstream_execution
            )  # EmptyContainer
            parameter_value_map = upstream_execution.call.lookup().parameter_value_map()
            destination_container = parameter_value_map["specification"]["value"]
        else:
            raise Exception(f'Invalid input pin "destination" for Transfer.')
        destination_name = None
        for deck, labware in self.configuration.items():
            if labware == destination_container:
                destination_name = f"labware{deck}"
                break
        if not destination_name:
            raise Exception(f"{destination_container} is not loaded.")

        # TODO: automatically choose pipette based on transferred volume
        if not self.configuration:
            raise Exception(
                "Transfer call failed. Use ConfigureInstrument to configure a pipette"
            )
        pipette = self.configuration["left"]

        source.container_type
        destination.container_type
        source.container_type.lookup

# make it a list with 5 elements (pick up, aspirate, dispense, return tips) this string when constructed will substitute variables declared by values on the protocol
        source_str = source.mask
        destination_str = destination.mask
        for c_source in get_sample_list(source.mask):
            for c_destination in get_sample_list(destination.mask):
                self.script_steps += f"""async def liquid_handling_sequence():
    await lh.pick_up_tips({primitive_tip_rack}[{source_str}])
      lh
    await lh.aspirate({source}[{source_str}],
        vols={value},
        flow_rates={100},
        end_delay=0.5,
        offsets=Coordinate(1, 2, 3))
    await lh.dispense({destination}[{destination_str}], vols={value})
    await lh.return_tips() """
# take information present in the primitive and construct string to be 
# make it a list with 5 elements (pick up, aspirate, dispense, return tips)
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

        # TODO: validate coordinates for the given container spec
        samples.source = slots
        samples.mask = coords
        container_str = get_container_name(container)

        rack_str = ""
        try:
            # TODO: replace this lookup with a call to get_token_source()
            rack = (
                slots.get_parent()
                .get_parent()
                .token_source.lookup()
                .node.lookup()
                .input_pin("specification")
                .value.value.lookup()
            )
            rack_str = get_container_name(rack)
        except Exception as e:
            print(e)

        aliquots = get_sample_list(coords)
        if len(aliquots) == 1:
            self.markdown_steps += [
                f"Load {container_str} in slot {coords} of {rack_str}"
            ]
        elif len(aliquots) > 1:
            self.markdown_steps += [
                f"Load {container_str}s in slots {coords} of {rack_str}"
            ]

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

        # Assume 96 well plate
        aliquots = get_sample_list(geometry="A1:H12")
        samples.initial_contents = json.dumps(
            xr.DataArray(aliquots, dims=("aliquot")).to_dict()
        )

        # upstream_ex = get_token_source('container', record)
        # container_spec = upstream_ex.call.lookup().parameter_value_map()['specification']['value']

        container_types = self.resolve_container_spec(container_spec)
        selected_container_type = self.check_lims_inventory(container_types)
        container_api_name = LABWARE_MAP[selected_container_type]
        container_str = get_container_name(container_spec)

        # TODO: need to specify instrument
        deck = self.get_instrument_deck(instrument)
        self.markdown_steps += [
            f"Load {container_str} in {slots} of Deck of pylabrobot instrument"
        ]
        self.script_steps += [
            f"labware{deck} = {instrument.display_id}.load_labware('{container_api_name}')"
        ]

        # Keep track of instrument configuration
        if not hasattr(instrument, "configuration"):
            instrument.configuration = {}
            for c in get_sample_list(slots):
                instrument.configuration[c] = container_spec

    def activate_airpump(self, record: labop.ActivityNodeExecution, ex: labop.ProtocolExecution):

       output_string = """ 
       comPort = 12
       BaudRate = 921600
        SimulationMode = 0
        options = 0
        FilterHeight = 14.9
        NozzleHeight = 14.9

        ControlPoints = "pressure, 0, 5;pressure, 10, 5;pressure, 15, 5;pressure, 20, 5;pressure, 30, 5;pressure, 40, 5;pressure, 50, 5; pressure, 60, 5"
        ReturnPlateToIntegrationArea = 1
        WasteContainerID = 0
        DisableVacuumCheck = 1



        async def MPE_overpressure():
        await MPE.mpe2_FilterPlatePlaced(MPE, 1, FilterHeight, NozzleHeight)
        await MPE.mpe2_ProcessFilterToWasteContainer(MPE, 1, ControlPoints,ReturnPlateToIntegrationArea, WasteContainerID, DisableVacuumCheck)
        await MPE.mpe2_FilterPlateRemoved(MPE, 1) 



        asyncio .run(__init__())
        asyncio .run(MPE_overpressure())"""        
       self.script_steps += [output_string]

