import logging
import json
import os 

import sbol3
import tyto

import paml
import uml
from paml_convert.behavior_specialization import BehaviorSpecialization
from paml_convert.markdown import MarkdownConverter


l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)

container_ontology_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../container-ontology/owl/container-ontology.ttl')
ContainerOntology = tyto.Ontology(path=container_ontology_path, uri='https://sift.net/container-ontology/container-ontology')


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
            "https://bioprotocols.org/paml/primitives/liquid_handling/Vortex": self.vortex,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Discard": self.discard,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Transfer": self.transfer,
            "https://bioprotocols.org/paml/primitives/culturing/Transform": self.transform,
            "https://bioprotocols.org/paml/primitives/culturing/Culture": self.culture,
            "https://bioprotocols.org/paml/primitives/plate_handling/Incubate": self.incubate,
            "https://bioprotocols.org/paml/primitives/plate_handling/Hold": self.hold,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Dilute": self.dilute,
            "https://bioprotocols.org/paml/primitives/liquid_handling/DiluteToTargetOD": self.dilute_to_target_od,
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
        #samples_var = parameter_value_map["samples"]['value']

        ## Define a container

        l.debug(f"define_container:")
        l.debug(f" specification: {spec}")
        #l.debug(f" samples: {samples_var}")

        try:
            possible_container_types = self.resolve_container_spec(spec)
            containers_str = ",".join([f"\n\t[{c.split('#')[1]}]({c})" for c in possible_container_types])
            self.markdown_steps += [f"Provision a container named `{spec.name}` such as: {containers_str}."]
        except Exception as e:
            l.warning(e)
            
            # Assume that a simple container class is specified, rather
            # than container properties.  Then use tyto to get the 
            # container label
            container_class = ContainerOntology.uri + '#' + spec.queryString.split(':')[-1]
            container_str = ContainerOntology.get_term_by_uri(container_class)
            self.markdown_steps += [f'Provision a {container_str} to contain `{spec.name}`']
            #except Exception as e:
            #    l.warning(e)
            #    self.markdown_steps += [f"Provision a container named `{spec.name}` meeting specification: {spec.queryString}."]

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
        #measurements = parameter_value_map["measurements"]["value"]

        # HACK extract contrainer from well group since we do not have it as input
        container = None #wells[0].container

        l.debug(f"measure_absorbance:")
        l.debug(f"  container: {container}")
        l.debug(f"  samples: {samples}")
        l.debug(f"  wavelength: {wl.value} {wl_units}")

        # Add to markdown
        #samples_str = f"`{samples.source.lookup().value.lookup().value.name}({samples.mask})`"
        # Lookup sample container to get the container name, and use that
        # as the sample label
        samples_str = record.document.find(samples.container_type).value.name
        self.markdown_steps += [f'Make absorbance measurements of {samples_str} at {wl.value} {wl_units}.']

    def vortex(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        duration = None
        if 'duration' in parameter_value_map:
            duration_measure = parameter_value_map["duration"]["value"]
            duration_scalar = duration_measure.value
            duration_units = tyto.OM.get_term_by_uri(duration_measure.unit)
        samples = parameter_value_map["samples"]["value"]

        # Add to markdown
        text = f"Vortex {samples}"
        if duration:
            text += f' for {duration_scalar} {duration_units}'
        self.markdown_steps += [text]

    def discard(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        samples = parameter_value_map["samples"]["value"]
        amount = parameter_value_map['amount']['value']
        amount_units = tyto.OM.get_term_by_uri(amount.unit)

        # Add to markdown
        text = f"`Discard {amount} {amount_units} of {samples.name})`"
        self.markdown_steps += [text]

    def transfer(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map['source']['value']
        destination = parameter_value_map['destination']['value']
        amount_measure = parameter_value_map['amount']['value']
        amount_scalar = amount_measure.value
        amount_units = tyto.OM.get_term_by_uri(amount_measure.unit)
        if 'dispenseVelocity' in parameter_value_map:
            dispense_velocity = parameter_value_map['dispenseVelocity']['value']

        # Get destination container type
        container_spec = record.document.find(destination.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)

        # Add to markdown
        text = f"Transfer {amount_scalar} {amount_units} of `{source.name}` to {container_str}"
        self.markdown_steps += [text]

    def culture(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        inoculum = parameter_value_map['inoculum']['value']
        growth_medium = parameter_value_map['growth_medium']['value']
        volume = parameter_value_map['volume']['value']
        volume_scalar = volume.value
        volume_units = tyto.OM.get_term_by_uri(volume.unit)
        duration = parameter_value_map['duration']['value']
        duration_scalar = duration.value
        duration_units = tyto.OM.get_term_by_uri(duration.unit)
        orbital_shake_speed = parameter_value_map['orbital_shake_speed']['value']
        temperature = parameter_value_map['temperature']['value']
        temperature_scalar = temperature.value
        temperature_units = tyto.OM.get_term_by_uri(temperature.unit)
        container = parameter_value_map['container']['value']
        # Lookup sample container to get the container name, and use that
        # as the sample label
        container_str = record.document.find(container.container_type).value.name
        text = f'Inoculate `{inoculum.name}` into {volume_scalar} {volume_units} of {growth_medium.name} in {container_str} and grow for {measurement_to_text(duration)} at {measurement_to_text(temperature)} and {orbital_shake_speed.value} rpm.'
        self.markdown_steps += [text]

    def incubate(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map['location']['value']
        duration = parameter_value_map['duration']['value']
        shakingFrequency = parameter_value_map['shakingFrequency']['value']
        temperature = parameter_value_map['temperature']['value']
        text = f'Incubate {location.name} for {measurement_to_text(duration)} at {measurement_to_text(temperature)} at {shakingFrequency.value}.'
        self.markdown_steps += [text]

    def hold(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map['location']['value']
        temperature = parameter_value_map['temperature']['value']
        text = f'Hold `{location.name}` at {measurement_to_text(temperature)}.'
        self.markdown_steps += [text]

    def dilute_to_target_od(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map['source']['value']
        destination = parameter_value_map['destination']['value']
        diluent = parameter_value_map['diluent']['value']
        amount = parameter_value_map['amount']['value']
        target_od = parameter_value_map['target_od']['value']
        
        # Get destination container type
        container_spec = record.document.find(destination.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)
        text = f'Dilute `{source.name}` with {diluent.name} into {container_str} to a target OD of {target_od.value} and final volume of {measurement_to_text(amount)}.'
        self.markdown_steps += [text]

    def dilute(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map['source']['value']
        destination = parameter_value_map['destination']['value']
        diluent = parameter_value_map['diluent']['value']
        amount = parameter_value_map['amount']['value']
        dilution_factor = parameter_value_map['dilution_factor']['value']

        # Get destination container type
        container_spec = record.document.find(destination.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)

        text = f'Dilute `{source.name}` with {diluent.name} into the {container_str} at a 1:{dilution_factor} ratio and final volume of {measurement_to_text(amount)}.'
        self.markdown_steps += [text]

    def transform(self, record: paml.ActivityNodeExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        host = parameter_value_map['host']['value']
        dna = parameter_value_map['dna']['value']
        medium = parameter_value_map['selection_medium']['value']
        if 'amount' in parameter_value_map:
            amount_measure = parameter_value_map['amount']['value']
            amount_scalar = amount_measure.value
            amount_units = tyto.OM.get_term_by_uri(amount_measure.unit)

        #transformant = record.node.lookup().output_pin('transformants')
        transformant = parameter_value_map['transformants']['value']
        transformant.name = f'{host.name} + {dna.name} transformants'

        # Add to markdown
        text = f"Transform `{dna.name}` into `{host.name}` and plate transformants on {medium.name}."
        self.markdown_steps += [text]

def measurement_to_text(measure: sbol3.Measure):
    measurement_scalar = measure.value
    measurement_units = tyto.OM.get_term_by_uri(measure.unit)
    return f'{measurement_scalar} {measurement_units}'


