import logging

import sbol3
import tyto

import paml
import uml
from paml_convert.behavior_specialization import BehaviorSpecialization
from paml_convert.markdown import MarkdownConverter

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
            self.markdown += self._materials_markdown(protocol)
            self.markdown += self._inputs_markdown(self.execution.parameter_values)

    def _inputs_markdown(self, parameter_values):
        markdown = '\n\n## Protocol Inputs:\n'
        for i in parameter_values:
            parameter = i.parameter.lookup()
            if parameter.property_value.direction == uml.PARAMETER_IN:
                markdown += self._parameter_value_markdown(i)
        return markdown

    def _outputs_markdown(self, parameter_values):
        markdown = '\n\n## Protocol Outputs:\n'
        for i in parameter_values:
            parameter = i.parameter.lookup()
            if parameter.property_value.direction == uml.PARAMETER_OUT:
                markdown += self._parameter_value_markdown(i, True)
        return markdown

    def _materials_markdown(self, protocol):
        document_objects = protocol.document.objects
        components = [x for x in protocol.document.objects if isinstance(x, sbol3.component.Component)]
        materials = {x.name: x for x in components}
        markdown = '\n\n## Protocol Materials:\n'
        for name, material  in materials.items():
            markdown += f"* [{name}]({material.types[0]})\n"
        return markdown

    def _parameter_value_markdown(self, pv : paml.ParameterValue, is_output=False):
        parameter = pv.parameter.lookup().property_value
        value = pv.value.lookup().value if isinstance(pv.value, uml.LiteralReference) else pv.value.value
        units = tyto.OM.get_term_by_uri(value.unit) if isinstance(value, sbol3.om_unit.Measure) else None
        value = str(f"{value.value} {units}")  if units else str(value)
        if is_output:
            return f"* `{parameter.name}`"
        else:
            return f"* `{parameter.name}` = {value}"

    def _steps_markdown(self):
        markdown = '\n\n## Steps\n'
        for i, step in enumerate(self.markdown_steps):
            markdown += str(i + 1) + '. ' + step + '\n'
        return markdown

    def on_end(self):
        self.markdown += self._outputs_markdown(self.execution.parameter_values)
        self.markdown_steps += [self.reporting_step()]
        self.markdown += self._steps_markdown()
        with open(self.out_path, "w") as f:
            f.write(self.markdown)

    def reporting_step(self):
        output_parameters = []
        for i in self.execution.parameter_values:
            parameter = i.parameter.lookup()
            value = i.value.value
            if parameter.property_value.direction == uml.PARAMETER_OUT:
                output_parameters.append(f"`{parameter.property_value.name}` from `{value}`")
        output_parameters = ", ".join(output_parameters)
        return f"Report values for {output_parameters}."

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

        try:
            possible_container_types = possible_container_types = self.resolve_container_spec(spec)
            containers_str = ",".join([f"\n\t[{c.split('#')[1]}]({c})" for c in possible_container_types])
            self.markdown_steps += [f"Provision a container named `{samples_var.name}` such as: {containers_str}."]
        except Exception as e:
            l.warning(e)
            self.markdown_steps += [f"Provision a container named `{samples_var.name}` meeting specification: {spec.queryString}."]

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

        resource_str = f"[{resource.name}]({resource.types[0]})"
        destination_str = f"`{destination.source.lookup().value.lookup().value.name}({destination.mask})`"
        self.markdown_steps += [f"Pipette {value} {units} of {resource_str} into {destination_str}."]


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
        measurements = parameter_value_map["measurements"]["value"]

        # HACK extract contrainer from well group since we do not have it as input
        container = None #wells[0].container

        l.debug(f"measure_absorbance:")
        l.debug(f"  container: {container}")
        l.debug(f"  samples: {samples}")
        l.debug(f"  wavelength: {wl.value} {wl_units}")

        # Add to markdown

        samples_str = f"`{samples.source.lookup().value.lookup().value.name}({samples.mask})`"
        self.markdown_steps += [f'Make absorbance measurements (named `{measurements}`) of {samples_str} at {wl.value} {wl_units}.']
