import logging
import json
import os 
import json
from datetime import datetime
from urllib.parse import quote, unquote
from typing import Union, List
from collections.abc import Iterable


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
        self.var_to_entity = {}
        self.markdown_converter = None
        self.doc = None

    def initialize_protocol(self, execution: paml.ProtocolExecution):
        super().initialize_protocol(execution)
        print(f'Initializing execution {execution.display_id}')
        # Defines sections of the markdown document
        execution.header = ''
        execution.inputs = ''
        execution.outputs = ''
        execution.materials = ''
        execution.body = ''
        execution.markdown_steps = []

        # Contains the final, compiled markdown
        execution.markdown = ''

    def _init_behavior_func_map(self) -> dict:
        return {
            "https://bioprotocols.org/paml/primitives/sample_arrays/EmptyContainer": self.define_container,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Provision": self.provision_container,
            "https://bioprotocols.org/paml/primitives/sample_arrays/PlateCoordinates": self.plate_coordinates,
            "https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance": self.measure_absorbance,
            "https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureFluorescence": self.measure_fluorescence,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Vortex": self.vortex,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Discard": self.discard,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Transfer": self.transfer,
            "https://bioprotocols.org/paml/primitives/liquid_handling/TransferByMap": self.transfer_by_map,
            "https://bioprotocols.org/paml/primitives/culturing/Transform": self.transform,
            "https://bioprotocols.org/paml/primitives/culturing/Culture": self.culture,
            "https://bioprotocols.org/paml/primitives/plate_handling/Incubate": self.incubate,
            "https://bioprotocols.org/paml/primitives/plate_handling/Hold": self.hold,
            "https://bioprotocols.org/paml/primitives/plate_handling/HoldOnIce": self.hold_on_ice,
            "https://bioprotocols.org/paml/primitives/plate_handling/EvaporativeSeal": self.evaporative_seal,
            "https://bioprotocols.org/paml/primitives/liquid_handling/Dilute": self.dilute,
            "https://bioprotocols.org/paml/primitives/liquid_handling/DiluteToTargetOD": self.dilute_to_target_od,
            "https://bioprotocols.org/paml/primitives/sample_arrays/ContainerSet": self.define_containers,
            "https://bioprotocols.org/paml/primitives/liquid_handling/SerialDilution": self.serial_dilution,
            "https://bioprotocols.org/paml/primitives/sample_arrays/PoolSamples": self.pool_samples,
            "https://bioprotocols.org/paml/primitives/plate_handling/QuickSpin": self.quick_spin,
            "https://bioprotocols.org/paml/primitives/plate_handling/Unseal": self.unseal,
            "https://bioprotocols.org/paml/primitives/sample_arrays/EmbeddedImage": self.embedded_image,
            "http://bioprotocols.org/paml#Protocol": self.subprotocol_specialization,
            "https://bioprotocols.org/paml/primitives/culturing/CulturePlates": self.culture_plates,
            "https://bioprotocols.org/paml/primitives/culturing/PickColonies": self.pick_colonies,
        }

    def on_begin(self, execution):
        if execution:
            protocol = execution.protocol.lookup()
            self.markdown_converter = MarkdownConverter(protocol.document)

    def _header_markdown(self, protocol):
        header = '# ' + (protocol.display_id if (protocol.name is None) else protocol.name) + '\n'
        header += '\n'
        #header += '## Description:\n' + (
        #    'No description given' if protocol.description is None else protocol.description) + '\n'
        header += ('No description given' if protocol.description is None else protocol.description) + '\n'
        return header

    def _inputs_markdown(self, parameter_values, subprotocol_executions):
        markdown = '\n\n## Protocol Inputs:\n'
        markdown = ''
        for i in parameter_values:
            parameter = i.parameter.lookup()
            if parameter.property_value.direction == uml.PARAMETER_IN:
                markdown += self._parameter_value_markdown(i)
        for x in subprotocol_executions:
            markdown += x.inputs
        return markdown

    def _outputs_markdown(self, parameter_values, subprotocol_executions):
        markdown = '\n\n## Protocol Outputs:\n'
        markdown = ''
        for i in parameter_values:
            parameter = i.parameter.lookup()
            if parameter.property_value.direction == uml.PARAMETER_OUT:
                markdown += self._parameter_value_markdown(i, True)
        for x in subprotocol_executions:
            markdown += x.outputs
        return markdown

    def _materials_markdown(self, protocol, subprotocol_executions):
        document_objects = protocol.document.objects
        # TODO: Use different criteria for compiling Materials list based on ValueSpecifications for ValuePins
        components = [x for x in document_objects if isinstance(x, sbol3.component.Component)]
        # This is a hack to avoid listing Components that are dynamically generated
        # during protocol execution, e.g., transformants
        components = [x for x in components if tyto.SBO.functional_entity not in x.types]
        materials = {x.name: x for x in components}
        markdown = '\n\n## Protocol Materials:\n'
        markdown = ''
        for name, material  in materials.items():
            markdown += f"* [{name}]({material.types[0]})\n"
        for x in subprotocol_executions:
            markdown += x.materials
        return markdown

    def _parameter_value_markdown(self, pv : paml.ParameterValue, is_output=False):
        parameter = pv.parameter.lookup().property_value
        value = pv.value.value.lookup().name if isinstance(pv.value, uml.LiteralReference) else pv.value.value
        units = tyto.OM.get_term_by_uri(value.unit) if isinstance(value, sbol3.om_unit.Measure) else None
        value = str(f"{value.value} {units}")  if units else str(value)
        if is_output:
            return f"* `{value}`\n"
            #return f"* `{parameter.name}`"
        else:
            return f"* `{parameter.name}` = {value}"

    def _steps_markdown(self, execution: paml.ProtocolExecution, subprotocol_executions):
        markdown = '\n\n## Steps\n'
        markdown = ''
        for x in subprotocol_executions:
            markdown += '\n\n##' + x.header
            markdown +=  x.body
        for i, step in enumerate(execution.markdown_steps):
            markdown += str(i + 1) + '. ' + step + '\n'
        return markdown

    def on_end(self, execution: paml.ProtocolExecution):
        protocol = execution.protocol.lookup()
        subprotocol_executions = execution.get_subprotocol_executions()
        execution.header += self._header_markdown(protocol)
        execution.inputs += self._inputs_markdown(execution.parameter_values, subprotocol_executions)
        execution.outputs += self._outputs_markdown(execution.parameter_values, subprotocol_executions)
        execution.body = self._steps_markdown(execution, subprotocol_executions)
        execution.markdown_steps += [self.reporting_step(execution)]
        execution.markdown += execution.header

        if execution.inputs:
            execution.markdown += '\n\n## Protocol Inputs:\n'
            execution.markdown += execution.inputs

        if execution.outputs:
            execution.markdown += '\n\n## Protocol Outputs:\n'
            execution.markdown += execution.outputs

        execution.markdown += '\n\n## Protocol Materials:\n'
        execution.markdown += self._materials_markdown(protocol, subprotocol_executions)
        execution.markdown += '\n\n## Protocol Steps:\n'
        execution.markdown += self._steps_markdown(execution, subprotocol_executions)

        # Timestamp the protocol version
        dt = datetime.now()
        ts = datetime.timestamp(dt)
        execution.markdown += f'---\nTimestamp: {datetime.fromtimestamp(ts)}'

        # Print document version
        # This is a little bit kludgey, because version is not an official PAML property
        # of Protocol
        protocol = execution.protocol.lookup()
        if hasattr(protocol, 'version'):
            execution.markdown += f'---\nProtocol version: {protocol.version}'

        with open(self.out_path, "w") as f:
            f.write(execution.markdown)

    def reporting_step(self, execution: paml.ProtocolExecution):
        output_parameters = []
        for i in execution.parameter_values:
            parameter = i.parameter.lookup()
            value = i.value.value.lookup().name if isinstance(i.value, uml.LiteralReference) else i.value.value
            if parameter.property_value.direction == uml.PARAMETER_OUT:
                #output_parameters.append(f"`{parameter.property_value.name}` from `{value}`")
                output_parameters.append(f'`{value}`')
        output_parameters = ", ".join(output_parameters)
        return f"Import data for {output_parameters} into provided Excel file."

    def define_container(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
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
            execution.markdown_steps += [f"Provision a container named `{spec.name}` such as: {containers_str}."]
        except Exception as e:
            l.warning(e)
            
            # Assume that a simple container class is specified, rather
            # than container properties.  Then use tyto to get the 
            # container label
            container_class = ContainerOntology.uri + '#' + spec.queryString.split(':')[-1]
            container_str = ContainerOntology.get_term_by_uri(container_class)
            if container_class == f'{ContainerOntology.uri}#StockReagent':
                text = f'Provision the {container_str} containing `{spec.name}`'
            else:
                text = f'Provision a {container_str} to contain `{spec.name}`'
            text = add_description(record, text)
            execution.markdown_steps += [text]
            #except Exception as e:
            #    l.warning(e)
            #    execution.markdown_steps += [f"Provision a container named `{spec.name}` meeting specification: {spec.queryString}."]

        return results

    def define_containers(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        containers = parameter_value_map["specification"]["value"]
        samples = parameter_value_map["samples"]["value"]
        quantity = parameter_value_map["quantity"]["value"]
        replicates = parameter_value_map["replicates"]["value"] if "replicates" in parameter_value_map else 1
        samples.container_type = containers.get_parent().identity
        assert(type(containers) is paml.ContainerSpec)
        try:
            
            # Assume that a simple container class is specified, rather
            # than container properties.  Then use tyto to get the 
            # container label
            container_class = ContainerOntology.uri + '#' + containers.queryString.split(':')[-1]
            container_str = ContainerOntology.get_term_by_uri(container_class)
           
            if quantity > 1:
                if replicates > 1:
                    text = f'Provision a total of {quantity*replicates} x {container_str}s to contain {replicates} replicates each of `{containers.name}`'
                else:
                    text = f'Provision {quantity} x {container_str}s to contain `{containers.name}`'
            else:
                text = f'Provision a {container_str} to contain `{containers.name}`'
            text = add_description(record, text)
            execution.markdown_steps += [text]

            samples.name = containers.name
        except Exception as e:
            l.warning(e)
            execution.markdown_steps += [f"Provision a container named `{containers.name}` meeting specification: {containers.queryString}."]

    # def provision_container(self, wells: WellGroup, amounts = None, volumes = None, informatics = None) -> Provision:
    def provision_container(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
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
        execution.markdown_steps += [f"Pipette {value} {units} of {resource_str} into {destination_str}."]


        return results

    def plate_coordinates(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]["value"]
        #container = self.var_to_entity[source]
        coords = parameter_value_map["coordinates"]["value"]
        samples = parameter_value_map['samples']['value']
        samples.name = source.name
        samples.contents = source.contents

        self.var_to_entity[parameter_value_map['samples']["value"]] = coords
        l.debug(f"plate_coordinates:")
        l.debug(f"  source: {source}")
        l.debug(f"  coordinates: {coords}")

        return results

    def measure_absorbance(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        wl = parameter_value_map["wavelength"]["value"]
        wl_units = tyto.OM.get_term_by_uri(wl.unit)
        samples = parameter_value_map["samples"]["value"]
        measurements = parameter_value_map["measurements"]["value"]
        timepoints = parameter_value_map['timepoints']['value'] if 'timepoints' in parameter_value_map else None

        l.debug(f"measure_absorbance:")
        l.debug(f"  samples: {samples}")
        l.debug(f"  wavelength: {wl.value} {wl_units}")
        l.debug(f"  measurements: {measurements}")

        # Lookup sample container to get the container name, and use that
        # as the sample label
        if isinstance(samples, paml.SampleMask):
            # SampleMasks are generated by the PlateCoordinates primitive
            # Their source does not directly reference a SampleArray directly,
            # rather through a LiteralReference and LiteralIdentified
            samples = samples.source.lookup().value.lookup().value
        samples_str = record.document.find(samples.container_type).value.name

        timepoints_str = ''
        if timepoints:
            timepoints_str = ' at timepoints ' + ', '.join([measurement_to_text(m) for m in timepoints])

        # Provide an informative name for the measurements output
        action=record.node.lookup()
        if action.name:
            measurements.name = f'{action.name} measurements of {samples_str}{timepoints_str}'
            text = f'Measure {action.name} of `{samples_str}` at {wl.value} {wl_units}{timepoints_str}.'
        else:
            measurements.name = f'absorbance measurements of {samples_str}{timepoints_str}'
            text = f'Measure absorbance of `{samples_str}` at {wl.value} {wl_units}{timepoints_str}.'

        text = add_description(record, text)
        execution.markdown_steps += [text]

    def measure_fluorescence(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        excitation = parameter_value_map['excitationWavelength']['value']
        emission = parameter_value_map['emissionWavelength']['value']
        bandpass = parameter_value_map['emissionBandpassWidth']['value']
        samples = parameter_value_map['samples']['value']
        timepoints = parameter_value_map['timepoints']['value'] if 'timepoints' in parameter_value_map else None
        measurements = parameter_value_map["measurements"]["value"]

        # Lookup sample container to get the container name, and use that
        # as the sample label
        if isinstance(samples, paml.SampleMask):
            # SampleMasks are generated by the PlateCoordinates primitive
            # Their source does not directly reference a SampleArray directly,
            # rather through a LiteralReference and LiteralIdentified
            samples = samples.source.lookup().value.lookup().value
        samples_str = record.document.find(samples.container_type).value.name

        timepoints_str = ''
        if timepoints:
            timepoints_str = ' at timepoints ' + ', '.join([measurement_to_text(m) for m in timepoints])

        # Provide an informative name for the measurements output
        action = record.node.lookup()
        if action.name:
            measurements.name = f'{action.name} measurements of {samples_str}{timepoints_str}'
            text = f'Measure {action.name} of `{samples_str}` with excitation wavelength of {measurement_to_text(excitation)} and emission filter of {measurement_to_text(emission)} and {measurement_to_text(bandpass)} bandpass{timepoints_str}.'
        else:
            measurements.name = f'fluorescence measurements of {samples_str}'
            text = f'Measure fluorescence of `{samples_str}` with excitation wavelength of {measurement_to_text(excitation)} and emission filter of {measurement_to_text(emission)} and {measurement_to_text(bandpass)} bandpass{timepoints_str}.'

        text = add_description(record, text)

        # Add to markdown
        execution.markdown_steps += [text]


    def vortex(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        duration = None
        if 'duration' in parameter_value_map:
            duration_measure = parameter_value_map["duration"]["value"]
            duration_scalar = duration_measure.value
            duration_units = tyto.OM.get_term_by_uri(duration_measure.unit)
        samples = parameter_value_map["samples"]["value"]
        mixed_samples = parameter_value_map["mixed_samples"]["value"]
        mixed_samples.name = samples.name

        # Add to markdown
        text = f"Vortex {samples.name}"
        if duration:
            text += f' for {duration_scalar} {duration_units}'
        execution.markdown_steps += [text]

    def discard(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        samples = parameter_value_map["samples"]["value"]
        amount = parameter_value_map['amount']['value']

        # Get coordinates if this is a plate
        coordinates = ''
        if isinstance(samples, paml.SampleMask):
            coordinates = f'wells {samples.mask} of '
            # SampleMasks are generated by the PlateCoordinates primitive
            # Their source does not directly reference a SampleArray directly,
            # rather through a LiteralReference and LiteralIdentified
            samples = samples.source.lookup().value.lookup().value

        # Get the container specs
        container_spec = record.document.find(samples.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)

        # Add to markdown
        text = f"Discard {measurement_to_text(amount)} from {coordinates}{container_str} `{container_spec.name}`."
        text = add_description(record, text) 
        execution.markdown_steps += [text]

    def transfer(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map['source']['value']
        destination = parameter_value_map['destination']['value']
        samples = parameter_value_map['samples']['value'] if 'samples' in parameter_value_map else None
        destination_coordinates = parameter_value_map['coordinates']['value'] if 'coordinates' in parameter_value_map else ''
        replicates = parameter_value_map['replicates']['value'] if 'replicates' in parameter_value_map else 1
        temperature = parameter_value_map['temperature']['value'] if 'temperature' in parameter_value_map else None
        amount_measure = parameter_value_map['amount']['value']
        amount_scalar = amount_measure.value
        amount_units = tyto.OM.get_term_by_uri(amount_measure.unit)
        if 'dispenseVelocity' in parameter_value_map:
            dispense_velocity = parameter_value_map['dispenseVelocity']['value']

        source_coordinates = ''
        if isinstance(source, paml.SampleMask):
            source_coordinates = source.mask
            # Get the corresponding SampleArray. The source property does not directly reference a SampleArray,
            # rather through a LiteralReference and LiteralIdentified
            # (this seems to bend the official specification a little)
            source = source.source.lookup().value.lookup().value
        source_contents = read_sample_contents(source)
        if source_coordinates:
            source_contents = {source_coordinates: source_contents[source_coordinates]}

        if isinstance(destination, paml.SampleMask):
            # Currently SampleMasks are generated by the PlateCoordinates primitive
            destination_coordinates = destination.mask
            ## Since we are dealing with PlateCoordinates, try to get the wells
            #try:
            #    destination_coordinates = destination.get_parent().get_parent().token_source.lookup().node.lookup().input_pin('coordinates').value.value
            #    destination_coordinates = f'wells {destination_coordinates}'
            #except:
            #    pass

            # Get the corresponding SampleArray. The source property does not directly reference a SampleArray,
            # rather through a LiteralReference and LiteralIdentified
            # (this seems to bend the official specification a little)
            destination = destination.source.lookup().value.lookup().value
        #destination_contents = read_sample_contents(destination)
        #print('-------')
        #print(destination_coordinates)
        #print('Source contents: ', source_contents)
        #print('Initial destination contents: ', destination_contents)
        #if source_coordinates and destination_coordinates:
        #    destination_contents[destination_coordinates] = source_contents[source_coordinates]
        #elif destination_coordinates:
        #    destination_contents[destination_coordinates] = source_contents['1']  # source is assumed to be a Component
        #else:
        #    destination_contents = source_contents
        #print('Final destination contents: ', destination_contents) 
        #samples.contents = quote(json.dumps(destination_contents))

        # Get destination container type
        container_spec = record.document.find(destination.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)
        destination.name = container_spec.name

        ## Propagate source details to destination
        if isinstance(destination, paml.SampleArray):
            if isinstance(source, paml.SampleArray):
                # Do a complete transfer of all source contents
                destination.contents = write_sample_contents(source,
                                                             replicates=replicates)
            elif destination_coordinates:
                # Add more samples to a plate that already has contents
                contents = read_sample_contents(destination)
                contents[destination_coordinates] = source.identity
                destination.contents = quote(json.dumps(contents))
                #destination.contents = write_sample_contents(contents, replicates)

        # Add to markdown
        if destination_coordinates:
            destination_coordinates = f'wells {destination_coordinates} of '

        source_names = get_sample_names(source, error_msg='Transfer execution failed. All source Components must specify a name.')
        if len(source_names) == 1:
            text = f"Transfer {amount_scalar} {amount_units} of `{source_names[0]}` sample to {destination_coordinates} {container_str} `{container_spec.name}`."
        elif len(source_names) > 1:
            n_source = len(read_sample_contents(source))
            n_destination = n_source * replicates
            replicate_str = f'each of {replicates} replicate ' if replicates > 1 else ''
            text = f"Transfer {amount_scalar} {amount_units} of each of {n_source} `{source.name}` samples to {destination_coordinates}{replicate_str}{container_str} containers to contain a total of {n_destination} `{container_spec.name}` samples."
            # f' Repeat for the remaining {len(source_names)-1} `{container_spec.name}` samples.'
        if temperature:
            text += f' Maintain at {measurement_to_text(temperature)} during transfer.'
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def transfer_by_map(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map['source']['value']
        destination = parameter_value_map['destination']['value']
        temperature = parameter_value_map['temperature']['value'] if 'temperature' in parameter_value_map else None
        amount_measure = parameter_value_map['amount']['value']
        amount_scalar = amount_measure.value
        amount_units = tyto.OM.get_term_by_uri(amount_measure.unit)
        if 'dispenseVelocity' in parameter_value_map:
            dispense_velocity = parameter_value_map['dispenseVelocity']['value']
        plan = parameter_value_map['plan']['value']
        map = json.loads(unquote(plan.values))

        source_container = record.document.find(source.container_type).value

        container_spec = record.document.find(destination.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)

        # Propagate source details to destination
        source_contents = read_sample_contents(source)
        destination_contents = read_sample_contents(destination)

        try:
            for k, v in source_contents.items():
                destination_contents[map[k]] = v
        except:
            print(source_contents)
            raise KeyError()
        destination.contents = quote(json.dumps(destination_contents))
        source_names = get_sample_names(source, error_msg='Transfer execution failed. All source Components must specify a name.')

        # Add to markdown
        text = f"Transfer {amount_scalar} {amount_units} of each `{source_container.name}` sample to {container_str} `{container_spec.name}` in the wells indicated in the plate layout.\n"
        #text +=  '| Sample | Wells |\n'
        #text +=  '| --- | --- |\n'
        #for coordinates, uri in destination_contents.items():
        #    name = record.document.find(uri).name
        #    text += f'|{name}|{coordinates}|\n'

        if temperature:
            text += f' Maintain at {measurement_to_text(temperature)} during transfer.'

        execution.markdown_steps += [text]

    def culture(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        inocula = parameter_value_map['inoculum']['value']
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
        replicates = parameter_value_map['replicates']['value'] if 'replicates' in parameter_value_map else 1
        container = parameter_value_map['container']['value'] 

        # Generate markdown
        container_str = record.document.find(container.container_type).value.name 
        inocula_names = get_sample_names(inocula, error_msg='Culture execution failed. All input inoculum Components must specify a name.')
        text = f'Inoculate `{inocula_names[0]}` into {volume_scalar} {volume_units} of {growth_medium.name} in {container_str} and grow for {measurement_to_text(duration)} at {measurement_to_text(temperature)} and {orbital_shake_speed.value} rpm.'
        text += repeat_for_remaining_samples(inocula_names, repeat_msg=' Repeat this procedure for the other inocula: ')
        if replicates > 1:
            text = f'Inoculate {replicates} colonies of each transformant {inocula.name}, for a total of {replicates*len(inocula_names)} cultures. Inoculate each into {volume_scalar} {volume_units} of {growth_medium.name} in {container_str} and grow for {measurement_to_text(duration)} at {measurement_to_text(temperature)} and {orbital_shake_speed.value} rpm.'


        # Populate output SampleArray
        container.contents = write_sample_contents(inocula, replicates)
        execution.markdown_steps += [text]

    def incubate(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map['location']['value']
        duration = parameter_value_map['duration']['value']
        shakingFrequency = parameter_value_map['shakingFrequency']['value']
        temperature = parameter_value_map['temperature']['value']

        sample_names = get_sample_names(location, error_msg='Hold execution failed. All input locations must have a name specified')
        if len(sample_names) > 1:
            text = f'Incubate all `{location.name}` samples for {measurement_to_text(duration)} at {measurement_to_text(temperature)} at {shakingFrequency.value} rpm.'
        else:
            text = f'Incubate `{location.name}` for {measurement_to_text(duration)} at {measurement_to_text(temperature)} at {shakingFrequency.value} rpm.'

        execution.markdown_steps += [text]

    def hold(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map['location']['value']
        temperature = parameter_value_map['temperature']['value']

        if len(read_sample_contents(location)) > 1:
            text = f'Hold all `{location.name}` samples at {measurement_to_text(temperature)}.'
        else:
            text = f'Hold `{location.name}` at {measurement_to_text(temperature)}.'
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def hold_on_ice(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map['location']['value']

        if len(read_sample_contents(location)) > 1:
            text = f'Hold all `{location.name}` samples on ice.'
        else:
            text = f'Hold `{location.name}` on ice.'
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def dilute_to_target_od(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map['source']['value']
        destination = parameter_value_map['destination']['value']
        diluent = parameter_value_map['diluent']['value']
        amount = parameter_value_map['amount']['value']
        target_od = parameter_value_map['target_od']['value']
        temperature = parameter_value_map['temperature']['value'] if 'temperature' in parameter_value_map else None
        destination.contents = source.contents
       
        # Get destination container type
        container_spec = record.document.find(destination.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)

        sample_names = get_sample_names(source, error_msg='Dilute to target OD execution failed. All source Components must specify a name.')

        if len(sample_names) == 1: 
            text = f'Back-dilute `{sample_names[0]}` `{source.name}` with {diluent.name} into {container_str} to a target OD of {target_od.value} and final volume of {measurement_to_text(amount)}.'
        elif len(sample_names) > 1:
            text = f'Back-dilute each of {len(read_sample_contents(source))} `{source.name}` samples to a target OD of {target_od.value} using {diluent.name} as diluent to a final volume of {measurement_to_text(amount)}.'

        if temperature:
            text += f' Maintain at {measurement_to_text(temperature)} while performing dilutions.'
        execution.markdown_steps += [text]

    def dilute(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map['source']['value']
        destination = parameter_value_map['destination']['value']
        diluent = parameter_value_map['diluent']['value']
        amount = parameter_value_map['amount']['value']
        replicates = parameter_value_map['replicates']['value'] if 'replicates' in parameter_value_map else 1
        dilution_factor = parameter_value_map['dilution_factor']['value']
        temperature = parameter_value_map['temperature']['value'] if 'temperature' in parameter_value_map else None

        destination.contents = source.contents

        # Get destination container type
        container_spec = record.document.find(destination.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_text = ContainerOntology.get_term_by_uri(container_class)

        # Get sample names
        sample_names = get_sample_names(source, error_msg='Dilute execution failed. All source Components must specify a name.')

        replicate_text = ' and each of {replicates} replicates ' if replicates else ''
        if len(sample_names) == 1:
            text = f'Dilute `{sample_names[0]}`{replicate_text}`{source.name}` with {diluent.name} into the {container_text} at a 1:{dilution_factor} ratio and final volume of {measurement_to_text(amount)}.'
        elif len(sample_names) > 1:
            text = f'Dilute each of {replicates*len(sample_names)} `{source.name}` samples with {diluent.name} into the {container_text} at a 1:{dilution_factor} ratio and final volume of {measurement_to_text(amount)}.'
        #repeat_for_remaining_samples(sample_names, repeat_msg='Repeat for the remaining cultures:')

        if temperature:
            text += f' Maintain at {measurement_to_text(temperature)} while performing dilutions.'
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def transform(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        host = parameter_value_map['host']['value']
        dna = parameter_value_map['dna']['value']
        medium = parameter_value_map['selection_medium']['value']
        destination = parameter_value_map['destination']['value']
        if 'amount' in parameter_value_map:
            amount_measure = parameter_value_map['amount']['value']
            amount_scalar = amount_measure.value
            amount_units = tyto.OM.get_term_by_uri(amount_measure.unit)

        dna_names = get_sample_names(dna, error_msg='Transform execution failed. All input DNA Components must specify a name.')

        # Instantiate Components to represent transformants and populate
        # these into the output SampleArray
        transformants = parameter_value_map['transformants']['value']
        i_transformant = 1
        contents = {}
        for i_dna, dna_name in enumerate(dna_names):

            # Use a while loop to mint a unique URI for new Components
            UNIQUE_URI = False
            while not UNIQUE_URI:
                try:
                    strain = sbol3.Component(f'transformant{i_transformant}',
                                             sbol3.SBO_FUNCTIONAL_ENTITY,
                                             name=f'{host.name}+{dna_name} transformant')
                    record.document.add(strain)

                    # Populate the output SampleArray with the new strain instances
                    contents[i_dna+1] = strain.identity
                    UNIQUE_URI = True
                except:
                    i_transformant += 1
            i_transformant += 1
        transformants.contents = quote(json.dumps(contents))
        transformants.name = destination.name

        # Add to markdown
        text = f"Transform `{dna_names[0]}` DNA into `{host.name}` and plate transformants on {medium.name}."
        text += repeat_for_remaining_samples(dna_names, repeat_msg='Repeat for the remaining transformant DNA: ')
        text += f' Plate transformants on `{destination.name}` plates.'
        execution.markdown_steps += [text]

    def serial_dilution(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map['source']['value']
        destination = parameter_value_map['destination']['value']
        diluent = parameter_value_map['diluent']['value']
        amount = parameter_value_map['amount']['value']
        dilution_factor = parameter_value_map['dilution_factor']['value']
        series = parameter_value_map['series']['value']


        destination_coordinates = ''
        if isinstance(destination, paml.SampleMask):
            # SampleMasks are generated by the PlateCoordinates primitive
            # Their source does not directly reference a SampleArray directly,
            # rather through a LiteralReference and LiteralIdentified
            destination_coordinates = f' wells {destination.mask} of'
            destination = destination.source.lookup().value.lookup().value
        source_coordinates = ''
        if isinstance(source, paml.SampleMask):
            # SampleMasks are generated by the PlateCoordinates primitive
            # Their source does not directly reference a SampleArray directly,
            # rather through a LiteralReference and LiteralIdentified
            source_coordinates = source.mask
            source = source.source.lookup().value.lookup().value

        # Get destination container type
        container_spec = record.document.find(destination.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)

        # Update destination contents
        destination.contents = source.contents

        # Get sample names
        sample_names = get_sample_names(source, error_msg='Dilute execution failed. All source Components must specify a name.', coordinates=source_coordinates)
        text = f'Perform a series of {series} {dilution_factor}-fold dilutions on `{sample_names[0]}` using `{diluent.name}` as diluent to a final volume of {measurement_to_text(amount)} in {destination_coordinates} {container_str} `{container_spec.name}`.'
        if len(sample_names) > 1 and not coordinates:
            text += f' Repeat for the remaining {len(sample_names)-1} `{source.name}` samples.'
        #repeat_for_remaining_samples(sample_names, repeat_msg='Repeat for the remaining cultures:')
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def evaporative_seal(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map['location']['value']
        type = parameter_value_map['type']['value']

        # Get destination container type
        container_spec = record.document.find(location.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)

        text = f'Cover `{location.name}` samples in {container_str} with your choice of material to prevent evaporation.'
        execution.markdown_steps += [text]

    def unseal(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map['location']['value']

        # Get destination container type
        container_spec = record.document.find(location.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)

        text = f'Remove the seal from {container_str} containing `{location.name}` samples.'
        execution.markdown_steps += [text]

    def pool_samples(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map['source']['value']
        samples = parameter_value_map['samples']['value']
        destination = parameter_value_map['destination']['value']
        volume = parameter_value_map['volume']['value']
        source_contents = read_sample_contents(source)

        # Get destination container type
        container_spec = record.document.find(destination.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)

        # Condense replicates
        n_samples = len(source_contents)
        source_contents = list(dict.fromkeys(source_contents.values()))  # Remove replicates while preserving order, see Stack Overflow #53657523

        source_contents += source_contents  # This is a kludge to support the iGEM protocol, necessary because we don't have a good way to track replicates
        n_replicates = int(n_samples / len(source_contents))
        samples.contents = write_sample_contents(source_contents)
        samples.name = source.name

        text = f'Pool {measurement_to_text(volume)} from each of {n_replicates} replicate `{source.name}` samples into {container_str} `{container_spec.name}`.'
        execution.markdown_steps += [text]
        
    def quick_spin(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map['location']['value']

        # Get destination container type
        container_spec = record.document.find(location.container_type).value
        container_class = ContainerOntology.uri + '#' + container_spec.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_class)

        text = f'Perform a brief centrifugation on {container_str} containing `{container_spec.name}` samples.'
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def subprotocol_specialization(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        pass

    def embedded_image(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        image = parameter_value_map['image']['value']
        caption = parameter_value_map['caption']['value']

        text = f'\n\n![]({image})\n<p align="center">{caption}</p>\n'

        execution.markdown_steps[-1] += text

    def culture_plates(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        container = parameter_value_map['specification']['value']
        quantity = parameter_value_map['quantity']['value']
        growth_medium = parameter_value_map['growth_medium']['value']
        samples = parameter_value_map['samples']['value']

        # Get destination container type
        container_uri = ContainerOntology.uri + '#' + container.queryString.split(':')[-1]
        container_str = ContainerOntology.get_term_by_uri(container_uri)
        samples.name = container.name

        execution.markdown_steps += [f'Provision {quantity} x {container_str} containing {growth_medium.name} growth medium for culturing `{samples.name}`']

    def pick_colonies(self, record: paml.ActivityNodeExecution, execution: paml.ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        colonies = parameter_value_map['colonies']['value']
        quantity = parameter_value_map['quantity']['value']
        replicates = parameter_value_map['replicates']['value']
        samples = parameter_value_map['samples']['value']
        samples.contents = colonies.contents
        samples.name = colonies.name
        execution.markdown_steps += [f'Pick {replicates} colonies from each `{colonies.name}` plate.']




def measurement_to_text(measure: sbol3.Measure):
    measurement_scalar = measure.value
    measurement_units = tyto.OM.get_term_by_uri(measure.unit)
    return f'{measurement_scalar} {measurement_units}'

def get_sample_names(inputs: Union[paml.SampleArray, sbol3.Component], error_msg, coordinates=None) -> list[str]:
    # Since some behavior inputs may be specified as either a SampleArray or directly as a list 
    # of Components, this provides a convenient way to unpack a list of sample names
    input_names = []
    if isinstance(inputs, paml.SampleArray):
        if inputs.contents:
            contents = read_sample_contents(inputs)
            if coordinates:
                input_names = {inputs.document.find(contents[coordinates]).name}
            else:
                input_names = {inputs.document.find(c).name for c in contents.values()}
    elif isinstance(inputs, Iterable):
        input_names = {i.name for i in inputs}        
    else:
        input_names = {inputs.name}
    if not all([name is not None for name in input_names]):
        raise ValueError(error_msg)
    return sorted(input_names)

def repeat_for_remaining_samples(names: list[str], repeat_msg: str):
    # Helps convert multiple samples to natural language
    if len(names) == 1:
        return ''
    elif len(names) == 2:
        return f'{repeat_msg} {names[1]}'
    elif len(names) == 3:
        return f'{repeat_msg} {names[1]} and {names[2]}'
    else:
        remaining = ', '.join([f'`{name}`' for name in names[1:-1]])
        remaining += f', and `{names[-1]}`'
        return f' {repeat_msg} {remaining}.'

def get_sample_label(sample: paml.SampleCollection) -> str:
    # Lookup sample container to get the container name, and use that
    # as the sample label
    if isinstance(sample, paml.SampleMask):
        # SampleMasks are generated by the PlateCoordinates primitive
        # Their source does not directly reference a SampleArray directly,
        # rather through a LiteralReference and LiteralIdentified
        sample = sample.source.lookup().value.lookup().value
    return record.document.find(sample.container_type).value.name

def write_sample_contents(sample_array: Union[dict, List[sbol3.Component]], replicates=1) -> str:
    if isinstance(sample_array, paml.SampleArray):
        old_contents = read_sample_contents(sample_array)
        contents = []
        for r in range(replicates):
            for c in old_contents.values():
                contents.append(c)
                #sample_array.document.find(c).name += f' replicate {r}'
        contents = {i+1: c for i, c in enumerate(contents)}
    else:
        contents = {i+1: c for i, c in enumerate(sample_array) for r in range(replicates)}
    return quote(json.dumps(contents))

def read_sample_contents(sample_array: paml.SampleArray) -> dict:
    if not isinstance(sample_array, paml.SampleArray):
        return {'1': sample_array.identity}
    if sample_array.contents == 'https://github.com/synbiodex/pysbol3#missing':
        return {}
    if not sample_array.contents:
        return {}
    # De-serialize the contents field of a SampleArray
    return json.loads(unquote(sample_array.contents))

def add_description(record, text):
    description = record.node.lookup().description
    if description:
        text += f' {description}'
    return text
