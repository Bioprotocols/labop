import sbol3
import tyto

import logging

import paml
import uml
from paml_convert.behavior_specialization import BehaviorSpecialization
from paml_convert.markdown import MarkdownConverter
from paml_convert.markdown.markdown_primitives import spectrophotometry_absorbance_to_markdown
from paml_convert.markdown.protocol_to_markdown import markdown_input

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)

class MarkdownSpecialization(BehaviorSpecialization):
    def __init__(self, out_path) -> None:
        super().__init__()
        self.out_path = out_path
        self.markdown = ""
        self.var_to_entity = {}
        self.markdown_converter = None
        self.markdown_steps = []
        self.doc = None

    def _init_behavior_func_map(self) -> dict:
        return {
            "https://bioprotocols.org/paml/primitives/sample_arrays/EmptyContainer": self.define_container,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Provision": self.provision_container,
            "https://bioprotocols.org/paml/primitives/sample_arrays/PlateCoordinates": self.plate_coordinates,
            "https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance": self.measure_absorbance,
        }

    def on_begin(self):
        if self.execution:
            protocol = self.execution.protocol.lookup()
            self.markdown_converter = MarkdownConverter(protocol.document)
            self.markdown += self.markdown_converter.markdown_header(protocol)
            self.markdown += self._inputs_markdown(self.execution.parameter_values)

    def _inputs_markdown(self, parameter_values):
        markdown = '\n\n## Protocol Inputs:\n'
        for i in parameter_values:
            parameter = i.parameter.lookup()
            if parameter.direction == uml.PARAMETER_IN:
                markdown += self._parameter_value_markdown(i)
        return markdown

    def _outputs_markdown(self, parameter_values):
        markdown = '\n\n## Protocol Outputs:\n'
        for i in parameter_values:
            parameter = i.parameter.lookup()
            if parameter.direction == uml.PARAMETER_OUT:
                markdown += self._parameter_value_markdown(i)
        return markdown

    def _parameter_value_markdown(self, pv : paml.ParameterValue):
        parameter = pv.parameter.lookup()
        value = pv.value.lookup().value if isinstance(pv.value, uml.LiteralReference) else pv.value.value
        value = str(f"{value.value} ({value.unit})") if isinstance(value, sbol3.om_unit.Measure) else str(value)
        return "* " + parameter.name + " = " + value

    def _steps_markdown(self):
        markdown = '\n\n## Steps\n'
        for i, step in enumerate(self.markdown_steps):
            markdown += str(i + 1) + '. ' + step + '\n'
        return markdown

    def on_end(self):
        self.markdown += self._outputs_markdown(self.execution.parameter_values)
        self.markdown += self._steps_markdown()
        with open(self.out_path, "w") as f:
            f.write(self.markdown)

    def define_container(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        spec = parameter_value_map["specification"]['value']
        samples_var = parameter_value_map["samples"]['value']

        ## Define a container

        l.debug(f"define_container:")
        l.debug(f" specification: {spec}")
        l.debug(f" samples: {samples_var}")

        return results

    # def provision_container(self, wells: WellGroup, amounts = None, volumes = None, informatics = None) -> Provision:
    def provision_container(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        destination = parameter_value_map["destination"]["value"]
        #dest_wells = self.var_to_entity[destination]
        value = parameter_value_map["amount"]["value"].value
        units = parameter_value_map["amount"]["value"].unit
        units = tyto.OM.get_term_by_uri(units)
        resource = parameter_value_map["resource"]["value"]
        #resource = self.resolutions[resource]
        l.debug(f"provision_container:")
        l.debug(f" destination: {destination}")
        l.debug(f" amount: {value} {units}")
        l.debug(f" resource: {resource}")


        return results

    def plate_coordinates(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]["value"]
        #container = self.var_to_entity[source]
        coords = parameter_value_map["coordinates"]["value"]

        self.var_to_entity[parameter_value_map['samples']["value"]] = coords
        l.debug(f"plate_coordinates:")
        l.debug(f"  source: {source}")
        l.debug(f"  coordinates: {coords}")

        return results

    def measure_absorbance(self, record: paml.ActivityNodeExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        wl = parameter_value_map["wavelength"]["value"]
        wl_units = tyto.OM.get_term_by_uri(wl.unit)
        samples = parameter_value_map["samples"]["value"]
        #wells = self.var_to_entity[samples]

        # HACK extract contrainer from well group since we do not have it as input
        container = None #wells[0].container

        l.debug(f"measure_absorbance:")
        l.debug(f"  container: {container}")
        l.debug(f"  samples: {samples}")
        l.debug(f"  wavelength: {wl.value} {wl_units}")

        # Add to markdown

        self.markdown_steps += spectrophotometry_absorbance_to_markdown(record.node.lookup(), self.markdown_converter)
