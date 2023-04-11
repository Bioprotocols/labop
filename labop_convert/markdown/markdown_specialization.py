import json
import logging
import os
import subprocess
from collections.abc import Iterable
from datetime import datetime
from typing import List, Union
from urllib.parse import quote, unquote

import pandas as pd
import sbol3
import tyto
import xarray as xr

from labop import (
    ActivityNodeExecution,
    ContainerSpec,
    Dataset,
    ParameterValue,
    ProtocolExecution,
    SampleArray,
    SampleCollection,
    SampleMask,
    Strings,
    deserialize_sample_format,
)
from labop_convert.behavior_specialization import BehaviorSpecialization
from uml import (
    PARAMETER_IN,
    PARAMETER_OUT,
    CallBehaviorAction,
    LiteralSpecification,
    Parameter,
)

from .protocol_to_markdown import MarkdownConverter

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)

try:
    container_ontology_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "../../labop/container-ontology.ttl",
    )  # CI path
except:
    container_ontology_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "../../container-ontology/owl/container-ontology.ttl",
    )


ContainerOntology = tyto.Ontology(
    path=container_ontology_path,
    uri="https://sift.net/container-ontology/container-ontology",
)


class MarkdownSpecialization(BehaviorSpecialization):
    def __init__(self, out_file, sample_format=Strings.JSON) -> None:
        super().__init__()
        self.out_file = out_file
        self.var_to_entity = {}
        self.markdown_converter = None
        self.doc = None
        self.propagate_objects = False
        self.sample_format = sample_format

    def initialize_protocol(self, execution: ProtocolExecution, out_dir=None):
        super().initialize_protocol(execution, out_dir=out_dir)
        print(f"Initializing execution {execution.display_id}")
        # Defines sections of the markdown document
        execution.header = ""
        execution.inputs = ""
        execution.outputs = ""
        execution.materials = ""
        execution.body = ""
        execution.markdown_steps = []

        # Contains the final, compiled markdown
        execution.markdown = ""

    def _init_behavior_func_map(self) -> dict:
        return {
            "https://bioprotocols.org/labop/primitives/sample_arrays/EmptyContainer": self.define_container,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Provision": self.provision_container,
            "https://bioprotocols.org/labop/primitives/sample_arrays/PlateCoordinates": self.plate_coordinates,
            "https://bioprotocols.org/labop/primitives/spectrophotometry/MeasureAbsorbance": self.measure_absorbance,
            "https://bioprotocols.org/labop/primitives/spectrophotometry/MeasureFluorescence": self.measure_fluorescence,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Vortex": self.vortex,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Discard": self.discard,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Transfer": self.transfer,
            "https://bioprotocols.org/labop/primitives/liquid_handling/TransferByMap": self.transfer_by_map,
            "https://bioprotocols.org/labop/primitives/culturing/Transform": self.transform,
            "https://bioprotocols.org/labop/primitives/culturing/Culture": self.culture,
            "https://bioprotocols.org/labop/primitives/plate_handling/Incubate": self.incubate,
            "https://bioprotocols.org/labop/primitives/plate_handling/Hold": self.hold,
            "https://bioprotocols.org/labop/primitives/plate_handling/HoldOnIce": self.hold_on_ice,
            "https://bioprotocols.org/labop/primitives/plate_handling/EvaporativeSeal": self.evaporative_seal,
            "https://bioprotocols.org/labop/primitives/liquid_handling/Dilute": self.dilute,
            "https://bioprotocols.org/labop/primitives/liquid_handling/DiluteToTargetOD": self.dilute_to_target_od,
            "https://bioprotocols.org/labop/primitives/sample_arrays/ContainerSet": self.define_containers,
            "https://bioprotocols.org/labop/primitives/liquid_handling/SerialDilution": self.serial_dilution,
            "https://bioprotocols.org/labop/primitives/sample_arrays/PoolSamples": self.pool_samples,
            "https://bioprotocols.org/labop/primitives/plate_handling/QuickSpin": self.quick_spin,
            "https://bioprotocols.org/labop/primitives/plate_handling/Unseal": self.unseal,
            "https://bioprotocols.org/labop/primitives/sample_arrays/EmbeddedImage": self.embedded_image,
            "http://bioprotocols.org/labop#Protocol": self.subprotocol_specialization,
            "https://bioprotocols.org/labop/primitives/culturing/CulturePlates": self.culture_plates,
            "https://bioprotocols.org/labop/primitives/culturing/PickColonies": self.pick_colonies,
            "https://bioprotocols.org/labop/primitives/sample_arrays/ExcelMetadata": self.excel_metadata,
            "https://bioprotocols.org/labop/primitives/sample_arrays/JoinMetadata": self.join_metadata,
        }

    def on_begin(self, execution):
        if execution:
            protocol = execution.protocol.lookup()
            self.markdown_converter = MarkdownConverter(protocol.document)

    def _header_markdown(self, protocol):
        header = (
            "# "
            + (protocol.display_id if (protocol.name is None) else protocol.name)
            + "\n"
        )
        header += "\n"
        # header += '## Description:\n' + (
        #    'No description given' if protocol.description is None else protocol.description) + '\n'
        header += (
            "No description given"
            if protocol.description is None
            else protocol.description
        ) + "\n"
        return header

    def _inputs_markdown(
        self, parameter_values, unbound_input_parameters, subprotocol_executions
    ):
        markdown = "\n\n## Protocol Inputs:\n"
        markdown = ""
        for i in parameter_values:
            parameter = i.parameter.lookup()
            if parameter.property_value.direction == PARAMETER_IN:
                markdown += self._parameter_value_markdown(i)
        for parameter in unbound_input_parameters:
            markdown += self._parameter_markdown(parameter)
        for x in subprotocol_executions:
            markdown += x.inputs
        return markdown

    def _outputs_markdown(
        self,
        parameter_values,
        unbound_output_parameters,
        subprotocol_executions,
    ):
        markdown = "\n\n## Protocol Outputs:\n"
        markdown = ""
        for i in parameter_values:
            parameter = i.parameter.lookup()
            if parameter.property_value.direction == PARAMETER_OUT:
                markdown += self._parameter_value_markdown(i, True)
        for parameter in unbound_output_parameters:
            markdown += self._parameter_markdown(parameter)
        for x in subprotocol_executions:
            markdown += x.outputs
        return markdown

    def _materials_markdown(self, protocol, subprotocol_executions):
        document_objects = protocol.document.objects
        # TODO: Use different criteria for compiling Materials list based on ValueSpecifications for ValuePins
        components = [
            x for x in document_objects if isinstance(x, sbol3.component.Component)
        ]
        # This is a hack to avoid listing Components that are dynamically generated
        # during protocol execution, e.g., transformants
        components = [
            x for x in components if tyto.SBO.functional_entity not in x.types
        ]
        materials = {x.name: x for x in components}
        markdown = "\n\n## Protocol Materials:\n"
        markdown = ""
        for name, material in materials.items():
            markdown += f"* [{name}]({material.types[0]})\n"

        # Compute container types and quantities
        document_objects = []
        protocol.document.traverse(lambda obj: document_objects.append(obj))
        call_behavior_actions = [
            obj for obj in document_objects if type(obj) is CallBehaviorAction
        ]
        containers = {}
        for cba in call_behavior_actions:
            try:
                pin = cba.input_pin("specification")
            except:
                continue
            container_type = pin.value.value.lookup().queryString

            try:
                pin = cba.input_pin("quantity")
            except:
                pin = None
            qty = pin.value.value if pin else 1

            if container_type in containers:
                containers[container_type] += qty
            else:
                containers[container_type] = qty

        for container_type, qty in containers.items():
            try:
                container_class = (
                    ContainerOntology.uri + "#" + container_type.split(":")[-1]
                )
                container_str = ContainerOntology.get_term_by_uri(container_class)
                text = f"* {container_str}"
                if qty > 1:
                    text += f" (x {qty})"
                text += "\n"
                markdown += text
            except:
                pass

        for x in subprotocol_executions:
            markdown += x.materials
        return markdown

    def _parameter_value_markdown(self, pv: ParameterValue, is_output=False):
        parameter = pv.parameter.lookup().property_value
        value = pv.value
        if isinstance(value, sbol3.Measure):
            value = measurement_to_text(value)
        elif isinstance(value, Dataset):
            value = value.get_value()
            value = self.dataset_to_text(value)
            return f"* {value}\n"
        elif isinstance(value, sbol3.Identified):
            value = parameter.name
        if is_output:
            return f"* `{value}`\n"
        else:
            return f"* `{parameter.name}` = {value}\n"

    def _parameter_markdown(self, p: Parameter):
        return f"* `{p.name}`\n"

    def _steps_markdown(self, execution: ProtocolExecution, subprotocol_executions):
        markdown = "\n\n## Steps\n"
        markdown = ""
        for x in subprotocol_executions:
            markdown += "\n\n##" + x.header
            markdown += x.body
        for i, step in enumerate(execution.markdown_steps):
            markdown += str(i + 1) + ". " + step + "\n"
        return markdown

    def on_end(self, execution: ProtocolExecution):
        protocol = execution.protocol.lookup()
        subprotocol_executions = execution.get_subprotocol_executions()
        execution.header += self._header_markdown(protocol)
        unbound_input_parameters = execution.unbound_inputs()
        execution.inputs += self._inputs_markdown(
            execution.parameter_values,
            unbound_input_parameters,
            subprotocol_executions,
        )
        unbound_output_parameters = execution.unbound_outputs()
        execution.outputs += self._outputs_markdown(
            execution.parameter_values,
            unbound_output_parameters,
            subprotocol_executions,
        )
        execution.body = self._steps_markdown(execution, subprotocol_executions)
        execution.markdown_steps += [self.reporting_step(execution)]
        execution.markdown += execution.header

        if execution.inputs:
            execution.markdown += "\n\n## Protocol Inputs:\n"
            execution.markdown += execution.inputs

        if execution.outputs:
            execution.markdown += "\n\n## Protocol Outputs:\n"
            execution.markdown += execution.outputs

        execution.markdown += "\n\n## Protocol Materials:\n"
        execution.markdown += self._materials_markdown(protocol, subprotocol_executions)
        execution.markdown += "\n\n## Protocol Steps:\n"
        execution.markdown += self._steps_markdown(execution, subprotocol_executions)

        # Timestamp the protocol version
        dt = datetime.now()
        ts = datetime.timestamp(dt)
        execution.markdown += f"---\nTimestamp: {datetime.fromtimestamp(ts)}"

        # Print document version
        # This is a little bit kludgey, because version is not an official LabOP property
        # of Protocol
        protocol = execution.protocol.lookup()
        if hasattr(protocol, "version"):
            execution.markdown += f"\nProtocol version: {protocol.version}"
        else:
            try:
                tag = subprocess.check_output(["git", "describe", "--tags"]).decode(
                    "utf-8"
                )
                execution.markdown += f"\nProtocol version: {tag}"
            except:
                pass
        execution.markdown += "\n"

        if self.out_file:
            if not os.path.exists(self.out_dir):
                os.mkdir(self.out_dir)
            with open(os.path.join(self.out_dir, self.out_file), "w") as f:
                f.write(execution.markdown)

        self.data = execution.markdown

    def reporting_step(self, execution: ProtocolExecution):
        output_parameters = []
        for i in execution.parameter_values:
            parameter = i.parameter.lookup()
            value = i.value
            if isinstance(value, LiteralSpecification):
                value = value.get_value()
            if isinstance(value, sbol3.Identified) and value.name:
                value = f"`{value.name}`"
            elif isinstance(value, Dataset):
                value = self.dataset_to_text(value)
            if parameter.property_value.direction == PARAMETER_OUT:
                output_parameters.append(f"{value}")
        output_parameters = ", ".join(output_parameters)
        return f"Import data into the provided Excel file: {output_parameters}."

    def define_container(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        spec = parameter_value_map["specification"]
        # samples_var = parameter_value_map["samples"]['value']

        ## Define a container

        l.debug(f"define_container:")
        l.debug(f" specification: {spec}")
        # l.debug(f" samples: {samples_var}")

        text = None
        try:
            possible_container_types = self.resolve_container_spec(spec)
            containers_str = ",".join(
                [f"\n\t[{c.split('#')[1]}]({c})" for c in possible_container_types]
            )
            text = (
                f"Provision a container named `{spec.name}` such as: {containers_str}."
            )
        except Exception as e:
            l.warning(e)

        if not text:
            try:
                # Assume that a simple container class is specified, rather
                # than container properties.  Then use tyto to get the
                # container label
                container_class = (
                    ContainerOntology.uri + "#" + spec.queryString.split(":")[-1]
                )
                container_str = ContainerOntology.get_term_by_uri(container_class)
                if container_class == f"{ContainerOntology.uri}#StockReagent":
                    text = f"Provision the {container_str} containing `{spec.name}`"
                else:
                    text = f"Obtain a {container_str} to contain `{spec.name}`"
                text = add_description(record, text)

            except Exception as e:
                l.warning(e)
        if not text:
            text = f"Provision a container named `{spec.name}` meeting specification: {spec.queryString}."
        execution.markdown_steps += [text]
        return results

    def define_containers(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        containers = parameter_value_map["specification"]
        samples = parameter_value_map["samples"]
        quantity = parameter_value_map["quantity"]
        replicates = (
            parameter_value_map["replicates"]
            if "replicates" in parameter_value_map
            else 1
        )
        samples.container_type = containers.identity

        # TODO: sample contents should be initialized by predefined handlers in
        # primitive_execution.py
        samples.initial_contents = quote(json.dumps({}))
        samples.format = "json"
        assert type(containers) is ContainerSpec
        try:
            # Assume that a simple container class is specified, rather
            # than container properties.  Then use tyto to get the
            # container label
            container_class = (
                ContainerOntology.uri + "#" + containers.queryString.split(":")[-1]
            )
            container_str = ContainerOntology.get_term_by_uri(container_class)

            if quantity > 1:
                if replicates > 1:
                    text = f"Obtain a total of {quantity*replicates} x {container_str}s to contain {replicates} replicates each of `{containers.name}`"
                else:
                    text = f"Obtain {quantity} x {container_str}s to contain `{containers.name}`"
            else:
                text = f"Obtain a {container_str} to contain `{containers.name}`"
            text = add_description(record, text)
            execution.markdown_steps += [text]

            samples.name = containers.name
        except Exception as e:
            l.warning(e)
            execution.markdown_steps += [
                f"Obtain a container named `{containers.name}` meeting specification: {containers.queryString}."
            ]

    def provision_container(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        destination = parameter_value_map["destination"]
        value = parameter_value_map["amount"].value
        units = parameter_value_map["amount"].unit
        units = tyto.OM.get_term_by_uri(units)
        resource = parameter_value_map["resource"]
        l.debug(f"provision_container:")
        l.debug(f" destination: {destination}")
        l.debug(f" amount: {value} {units}")
        l.debug(f" resource: {resource}")

        resource_str = f"[{resource.name}]({resource.types[0]})"
        destination_coordinates = ""
        if type(destination) == SampleMask:
            destination_coordinates = f"({destination.mask})"
            destination = destination.source.lookup()
        destination_str = f"`{destination.name} {destination_coordinates}`"
        execution.markdown_steps += [
            f"Pipette {value} {units} of {resource_str} into {destination_str}."
        ]

        return results

    def plate_coordinates(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]
        # container = self.var_to_entity[source]
        coords = parameter_value_map["coordinates"]
        samples = parameter_value_map["samples"]
        samples.name = source.name
        samples.initial_contents = source.initial_contents

        self.var_to_entity[parameter_value_map["samples"]] = coords
        l.debug(f"plate_coordinates:")
        l.debug(f"  source: {source}")
        l.debug(f"  coordinates: {coords}")

        return results

    def measure_absorbance(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        wl = parameter_value_map["wavelength"]
        wl_units = tyto.OM.get_term_by_uri(wl.unit)
        samples = parameter_value_map["samples"]
        measurements = parameter_value_map["measurements"]
        timepoints = (
            parameter_value_map["timepoints"]
            if "timepoints" in parameter_value_map
            else None
        )

        l.debug(f"measure_absorbance:")
        l.debug(f"  samples: {samples}")
        l.debug(f"  wavelength: {wl.value} {wl_units}")
        l.debug(f"  measurements: {measurements}")

        # Lookup sample container to get the container name, and use that
        # as the sample label
        if isinstance(samples, SampleMask):
            # SampleMasks are generated by the PlateCoordinates primitive
            # and we have to dereference the source to get the actual
            # SampleArray
            samples = samples.source.lookup()
        samples_str = record.document.find(samples.container_type).name

        timepoints_str = ""
        if timepoints:
            timepoints_str = " at timepoints " + ", ".join(
                [measurement_to_text(m) for m in timepoints]
            )

        # Provide an informative name for the measurements output
        action = record.node.lookup()
        if action.name:
            measurements.name = (
                f"{action.name} measurements of {samples_str}{timepoints_str}"
            )
            text = f"Measure {action.name} of `{samples_str}` at {wl.value} {wl_units}{timepoints_str}."
        else:
            measurements.name = (
                f"absorbance measurements of {samples_str}{timepoints_str}"
            )
            text = f"Measure absorbance of `{samples_str}` at {wl.value} {wl_units}{timepoints_str}."

        text = add_description(record, text)
        execution.markdown_steps += [text]

    def measure_fluorescence(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        results = {}
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        excitation = parameter_value_map["excitationWavelength"]
        emission = parameter_value_map["emissionWavelength"]
        bandpass = parameter_value_map["emissionBandpassWidth"]
        samples = parameter_value_map["samples"]
        timepoints = (
            parameter_value_map["timepoints"]
            if "timepoints" in parameter_value_map
            else None
        )
        measurements = parameter_value_map["measurements"]

        # Lookup sample container to get the container name, and use that
        # as the sample label
        if isinstance(samples, SampleMask):
            samples = samples.source.lookup()
        samples_str = record.document.find(samples.container_type).name

        timepoints_str = ""
        if timepoints:
            timepoints_str = " at timepoints " + ", ".join(
                [measurement_to_text(m) for m in timepoints]
            )

        # Provide an informative name for the measurements output
        action = record.node.lookup()
        if action.name:
            measurements.name = (
                f"{action.name} measurements of {samples_str}{timepoints_str}"
            )
            text = f"Measure {action.name} of `{samples_str}` with excitation wavelength of {measurement_to_text(excitation)} and emission filter of {measurement_to_text(emission)} and {measurement_to_text(bandpass)} bandpass{timepoints_str}."
        else:
            measurements.name = f"fluorescence measurements of {samples_str}"
            text = f"Measure fluorescence of `{samples_str}` with excitation wavelength of {measurement_to_text(excitation)} and emission filter of {measurement_to_text(emission)} and {measurement_to_text(bandpass)} bandpass{timepoints_str}."

        text = add_description(record, text)

        # Add to markdown
        execution.markdown_steps += [text]

    def vortex(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        duration = None
        if "duration" in parameter_value_map:
            duration_measure = parameter_value_map["duration"]
            duration_scalar = duration_measure.value
            duration_units = tyto.OM.get_term_by_uri(duration_measure.unit)
        samples = parameter_value_map["samples"]
        mixed_samples = parameter_value_map["mixed_samples"]
        mixed_samples.name = samples.name

        # Add to markdown
        text = f"Vortex {samples.name}"
        if duration:
            text += f" for {duration_scalar} {duration_units}"
        execution.markdown_steps += [text]

    def discard(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        samples = parameter_value_map["samples"]
        amount = parameter_value_map["amount"]

        # Get coordinates if this is a plate
        coordinates = ""
        if isinstance(samples, SampleMask):
            coordinates = f"wells {samples.sample_coordinates(sample_format=self.sample_format)} of "
            samples = samples.source.lookup()

        # Get the container specs
        container_spec = record.document.find(samples.container_type)
        container_class = (
            ContainerOntology.uri + "#" + container_spec.queryString.split(":")[-1]
        )
        container_str = ContainerOntology.get_term_by_uri(container_class)

        # Add to markdown
        text = f"Discard {measurement_to_text(amount)} from {coordinates}{container_str} `{container_spec.name}`."
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def transfer(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]
        destination = parameter_value_map["destination"]
        samples = (
            parameter_value_map["samples"] if "samples" in parameter_value_map else None
        )
        destination_coordinates = (
            parameter_value_map["coordinates"]
            if "coordinates" in parameter_value_map
            else ""
        )
        replicates = (
            parameter_value_map["replicates"]
            if "replicates" in parameter_value_map
            else 1
        )
        temperature = (
            parameter_value_map["temperature"]
            if "temperature" in parameter_value_map
            else None
        )
        amount_measure = parameter_value_map["amount"]
        amount_scalar = amount_measure.value
        amount_units = tyto.OM.get_term_by_uri(amount_measure.unit)
        if "dispenseVelocity" in parameter_value_map:
            dispense_velocity = parameter_value_map["dispenseVelocity"]

        source_coordinates = ""
        if isinstance(source, SampleMask):
            source_coordinates = source.mask
            source = source.source.lookup()
        source_contents = read_sample_contents(source)
        if source_coordinates:
            source_contents = {source_coordinates: source_contents[source_coordinates]}

        if isinstance(destination, SampleArray):
            # Currently SampleMasks are generated by the PlateCoordinates primitive
            destination_coordinates = deserialize_sample_format(
                destination.initial_contents, parent=destination
            )
        elif isinstance(destination, SampleMask):
            destination_coordinates = destination.to_masked_data_array()
            destination = destination.source.lookup()

        # destination_contents = read_sample_contents(destination)
        # print('-------')
        # print(destination_coordinates)
        # print('Source contents: ', source_contents)
        # print('Initial destination contents: ', destination_contents)
        # if source_coordinates and destination_coordinates:
        #    destination_contents[destination_coordinates] = source_contents[source_coordinates]
        # elif destination_coordinates:
        #    destination_contents[destination_coordinates] = source_contents['1']  # source is assumed to be a Component
        # else:
        #    destination_contents = source_contents
        # print('Final destination contents: ', destination_contents)
        # samples.initial_contents = quote(json.dumps(destination_contents))

        # Get destination container type
        container_spec = record.document.find(destination.container_type)
        container_class = (
            ContainerOntology.uri + "#" + container_spec.queryString.split(":")[-1]
        )
        container_str = ContainerOntology.get_term_by_uri(container_class)
        destination.name = container_spec.name

        if self.propagate_objects:
            ## Propagate source details to destination
            if isinstance(destination, SampleArray):
                if isinstance(source, SampleArray):
                    # Do a complete transfer of all source contents
                    destination.initial_contents = write_sample_contents(
                        source, replicates=replicates
                    )
                else:
                    # Add more samples to a plate that already has contents
                    initial_contents = read_sample_contents(destination)
                    initial_contents[destination_coordinates] = source.identity
                    destination.initial_contents = quote(json.dumps(initial_contents))
                    # destination.initial_contents = write_sample_contents(initial_contents, replicates)

        # Add to markdown
        if destination_coordinates is not None:
            destination_coordinates = f"wells {destination.sample_coordinates(sample_format=self.sample_format)} of "

        source_names = get_sample_names(
            source,
            error_msg="Transfer execution failed. All source Components must specify a name.",
        )
        if len(source_names) == 0:
            text = f"Transfer {amount_scalar} {amount_units} of `{source.name}` sample to {destination_coordinates} {container_str} `{container_spec.name}`."

        elif len(source_names) == 1:
            text = f"Transfer {amount_scalar} {amount_units} of `{source_names[0]}` sample to {destination_coordinates} {container_str} `{container_spec.name}`."
        elif len(source_names) > 1:
            n_source = len(read_sample_contents(source))
            n_destination = n_source * replicates
            replicate_str = f"each of {replicates} replicate " if replicates > 1 else ""
            text = f"Transfer {amount_scalar} {amount_units} of each of {n_source} `{source.name}` samples to {destination_coordinates}{replicate_str}{container_str} containers to contain a total of {n_destination} `{container_spec.name}` samples."
            # f' Repeat for the remaining {len(source_names)-1} `{container_spec.name}` samples.'
        if temperature:
            text += f" Maintain at {measurement_to_text(temperature)} during transfer."
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def transfer_by_map(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]
        destination = parameter_value_map["destination"]
        temperature = (
            parameter_value_map["temperature"]
            if "temperature" in parameter_value_map
            else None
        )
        amount_measure = parameter_value_map["amount"]
        amount_scalar = amount_measure.value
        amount_units = tyto.OM.get_term_by_uri(amount_measure.unit)
        if "dispenseVelocity" in parameter_value_map:
            dispense_velocity = parameter_value_map["dispenseVelocity"]
        plan = parameter_value_map["plan"]
        if plan:
            map = json.loads(unquote(plan.values))

            # Propagate source details to destination
            source_contents = read_sample_contents(source)
            destination_contents = read_sample_contents(destination)

            try:
                for k, v in source_contents.items():
                    destination_contents[map[k]] = v
            except:
                print(source_contents)
                raise KeyError()
            destination.initial_contents = quote(json.dumps(destination_contents))
        else:
            l.warn(f"Cannot instantiate a map for TransferByMap because plan is None")

        if source:
            source_container = record.document.find(source.container_type)
            source_names = get_sample_names(
                source,
                error_msg="Transfer execution failed. All source Components must specify a name.",
            )
        else:
            source_container = None

        if destination:
            container_spec = record.document.find(destination.container_type)
            container_class = (
                ContainerOntology.uri + "#" + container_spec.queryString.split(":")[-1]
            )
            container_str = ContainerOntology.get_term_by_uri(container_class)
        else:
            container_str = None
            container_spec = None

        # Add to markdown
        if (
            amount_scalar
            and amount_units
            and source_container
            and container_str
            and container_spec
        ):
            text = f"Transfer {amount_scalar} {amount_units} of each `{source_container.name}` sample to {container_str} `{container_spec.name}` in the wells indicated in the plate layout.\n"
            # text +=  '| Sample | Wells |\n'
            # text +=  '| --- | --- |\n'
            # for coordinates, uri in destination_contents.items():
            #    name = record.document.find(uri).name
            #    text += f'|{name}|{coordinates}|\n'
        elif amount_scalar and amount_units:
            text = f"Transfer {amount_scalar} {amount_units} of each *source* sample to *destination*.\n"
        else:
            text = f"TransferByMap (*could not specialize activity*).\n"

        if temperature:
            text += f" Maintain at {measurement_to_text(temperature)} during transfer."

        execution.markdown_steps += [text]

    def culture(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        inocula = parameter_value_map["inoculum"]
        growth_medium = parameter_value_map["growth_medium"]
        volume = parameter_value_map["volume"]
        volume_scalar = volume.value
        volume_units = tyto.OM.get_term_by_uri(volume.unit)
        duration = parameter_value_map["duration"]
        duration_scalar = duration.value
        duration_units = tyto.OM.get_term_by_uri(duration.unit)
        orbital_shake_speed = parameter_value_map["orbital_shake_speed"]["value"]
        temperature = parameter_value_map["temperature"]
        temperature_scalar = temperature.value
        temperature_units = tyto.OM.get_term_by_uri(temperature.unit)
        replicates = (
            parameter_value_map["replicates"]
            if "replicates" in parameter_value_map
            else 1
        )
        container = parameter_value_map["container"]

        # Generate markdown
        container_str = record.document.find(container.container_type).name
        inocula_names = get_sample_names(
            inocula,
            error_msg="Culture execution failed. All input inoculum Components must specify a name.",
        )
        # text = f'Inoculate `{inocula_names[0]}` into {volume_scalar} {volume_units} of {growth_medium.name} in {container_str} and grow for {measurement_to_text(duration)} at {measurement_to_text(temperature)} and {int(orbital_shake_speed.value)} rpm.'
        if duration_scalar > 14:
            text = f"Inoculate `{inocula_names[0]}` into {volume_scalar} {volume_units} of {growth_medium.name} in {container_str} and grow overnight (for {measurement_to_text(duration)}) at {measurement_to_text(temperature)} and {int(orbital_shake_speed.value)} rpm."
        else:
            text = f"Inoculate `{inocula_names[0]}` into {volume_scalar} {volume_units} of {growth_medium.name} in {container_str} and grow for {measurement_to_text(duration)} at {measurement_to_text(temperature)} and {int(orbital_shake_speed.value)} rpm."
        text += repeat_for_remaining_samples(
            inocula_names,
            repeat_msg=" Repeat this procedure for the other inocula: ",
        )
        if replicates > 1:
            if duration_scalar > 14:
                text = f"Inoculate {replicates} colonies of each {inocula.name}, for a total of {replicates*len(inocula_names)} cultures. Inoculate each into {volume_scalar} {volume_units} of {growth_medium.name} in {container_str} and grow overnight (for {measurement_to_text(duration)}) at {measurement_to_text(temperature)} and {int(orbital_shake_speed.value)} rpm."
            else:
                text = f"Inoculate {replicates} colonies of each {inocula.name}, for a total of {replicates*len(inocula_names)} cultures. Inoculate each into {volume_scalar} {volume_units} of {growth_medium.name} in {container_str} and grow for {measurement_to_text(duration)} at {measurement_to_text(temperature)} and {int(orbital_shake_speed.value)} rpm."

        # Populate output SampleArray
        container.initial_contents = write_sample_contents(inocula, replicates)
        execution.markdown_steps += [text]

    def incubate(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map["location"]
        duration = parameter_value_map["duration"]
        shakingFrequency = parameter_value_map["shakingFrequency"]
        temperature = parameter_value_map["temperature"]

        sample_names = get_sample_names(
            location,
            error_msg="Hold execution failed. All input locations must have a name specified",
        )
        if len(sample_names) > 1:
            text = f"Incubate all `{location.name}` samples for {measurement_to_text(duration)} at {measurement_to_text(temperature)} at {int(shakingFrequency.value)} rpm."
        else:
            text = f"Incubate `{location.name}` for {measurement_to_text(duration)} at {measurement_to_text(temperature)} at {int(shakingFrequency.value)} rpm."

        execution.markdown_steps += [text]

    def hold(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map["location"]
        temperature = parameter_value_map["temperature"]

        if len(read_sample_contents(location)) > 1:
            text = f"Hold all `{location.name}` samples at {measurement_to_text(temperature)}."
        else:
            text = f"Hold `{location.name}` at {measurement_to_text(temperature)}."
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def hold_on_ice(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map["location"]

        if len(read_sample_contents(location)) > 1:
            text = f"Hold all `{location.name}` samples on ice."
        else:
            text = f"Hold `{location.name}` on ice."
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def dilute_to_target_od(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]
        destination = parameter_value_map["destination"]
        diluent = parameter_value_map["diluent"]
        amount = parameter_value_map["amount"]
        target_od = parameter_value_map["target_od"]
        temperature = (
            parameter_value_map["temperature"]
            if "temperature" in parameter_value_map
            else None
        )
        destination.initial_contents = source.initial_contents

        # Get destination container type
        container_spec = record.document.find(destination.container_type)
        container_class = (
            ContainerOntology.uri + "#" + container_spec.queryString.split(":")[-1]
        )
        container_str = ContainerOntology.get_term_by_uri(container_class)

        sample_names = get_sample_names(
            source,
            error_msg="Dilute to target OD execution failed. All source Components must specify a name.",
        )

        if len(sample_names) == 1:
            text = f"Back-dilute `{sample_names[0]}` `{source.name}` with {diluent.name} into {container_str} to a target OD of {target_od.value} and final volume of {measurement_to_text(amount)}."
        elif len(sample_names) > 1:
            text = f"Back-dilute each of {len(read_sample_contents(source))} `{source.name}` samples to a target OD of {target_od.value} using {diluent.name} as diluent to a final volume of {measurement_to_text(amount)}."

        if temperature:
            text += f" Maintain at {measurement_to_text(temperature)} while performing dilutions."
        execution.markdown_steps += [text]

    def dilute(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]
        destination = parameter_value_map["destination"]
        diluent = parameter_value_map["diluent"]
        amount = parameter_value_map["amount"]
        replicates = (
            parameter_value_map["replicates"]
            if "replicates" in parameter_value_map
            else 1
        )
        dilution_factor = parameter_value_map["dilution_factor"]
        temperature = (
            parameter_value_map["temperature"]
            if "temperature" in parameter_value_map
            else None
        )

        destination.initial_contents = source.initial_contents

        # Get destination container type
        container_spec = record.document.find(destination.container_type)
        container_class = (
            ContainerOntology.uri + "#" + container_spec.queryString.split(":")[-1]
        )
        container_text = ContainerOntology.get_term_by_uri(container_class)

        # Get sample names
        sample_names = get_sample_names(
            source,
            error_msg="Dilute execution failed. All source Components must specify a name.",
        )

        replicate_text = " and each of {replicates} replicates " if replicates else ""
        if len(sample_names) == 1:
            text = f"Dilute `{sample_names[0]}`{replicate_text}`{source.name}` with {diluent.name} into the {container_text} at a 1:{dilution_factor} ratio and final volume of {measurement_to_text(amount)}."
        elif len(sample_names) > 1:
            text = f"Dilute each of {replicates*len(sample_names)} `{source.name}` samples with {diluent.name} into the {container_text} at a 1:{dilution_factor} ratio and final volume of {measurement_to_text(amount)}."
        # repeat_for_remaining_samples(sample_names, repeat_msg='Repeat for the remaining cultures:')

        if temperature:
            text += f" Maintain at {measurement_to_text(temperature)} while performing dilutions."
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def transform(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        host = parameter_value_map["host"]
        dna = parameter_value_map["dna"]
        medium = parameter_value_map["selection_medium"]
        destination = parameter_value_map["destination"]
        transformants = parameter_value_map["transformants"]
        if "amount" in parameter_value_map:
            amount_measure = parameter_value_map["amount"]
            amount_scalar = amount_measure.value
            amount_units = tyto.OM.get_term_by_uri(amount_measure.unit)

        dna_names = get_sample_names(
            dna,
            error_msg="Transform execution failed. All input DNA Components must specify a name.",
        )

        # TODO: move this initialization to predefined primitives
        transformants.format = "json"

        # Instantiate Components to represent transformants and populate
        # these into the output SampleArray
        i_transformant = 1
        initial_contents = {}
        for i_dna, dna_name in enumerate(dna_names):
            # Use a while loop to mint a unique URI for new Components
            UNIQUE_URI = False
            while not UNIQUE_URI:
                try:
                    strain = sbol3.Component(
                        f"transformant{i_transformant}",
                        sbol3.SBO_FUNCTIONAL_ENTITY,
                        name=f"{host.name}+{dna_name} transformant",
                    )
                    record.document.add(strain)

                    # Populate the output SampleArray with the new strain instances
                    initial_contents[i_dna + 1] = strain.identity
                    UNIQUE_URI = True
                except:
                    i_transformant += 1
            i_transformant += 1
        transformants.initial_contents = quote(json.dumps(initial_contents))
        transformants.name = destination.name

        # Add to markdown
        text = f"Transform `{dna_names[0]}` DNA into `{host.name}`."
        text += repeat_for_remaining_samples(
            dna_names, repeat_msg="Repeat for the remaining transformant DNA: "
        )
        text += f" Plate transformants on {medium.name} `{destination.name}` plates."
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def serial_dilution(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]
        destination = parameter_value_map["destination"]
        diluent = parameter_value_map["diluent"]
        amount = parameter_value_map["amount"]
        dilution_factor = parameter_value_map["dilution_factor"]
        series = parameter_value_map["series"]

        destination_coordinates = ""
        if isinstance(destination, SampleMask):
            destination_coordinates = f" wells {deserialize_sample_format(destination.mask, destination)[Strings.SAMPLE].data.tolist()} of"
            destination = destination.source.lookup()
        source_coordinates = source.sample_coordinates(sample_format=self.sample_format)
        if isinstance(source, SampleMask):
            source = source.source.lookup()

        # Get destination container type
        container_spec = record.document.find(destination.container_type)
        container_class = (
            ContainerOntology.uri + "#" + container_spec.queryString.split(":")[-1]
        )
        container_str = ContainerOntology.get_term_by_uri(container_class)

        if self.propagate_objects:
            # Update destination contents
            destination.initial_contents = source.initial_contents

            # Get sample names
            sample_names = get_sample_names(
                source,
                error_msg="Dilute execution failed. All source Components must specify a name.",
                coordinates=source_coordinates,
            )
        else:
            sample_names = source_coordinates
        text = f"Perform a series of {series} {dilution_factor}-fold dilutions on `{sample_names[0]}` using `{diluent.name}` as diluent to a final volume of {measurement_to_text(amount)} in {destination_coordinates} {container_str} `{container_spec.name}`."
        if len(sample_names) > 1 and not source_coordinates:
            text += f" Repeat for the remaining {len(sample_names)-1} `{source.name}` samples."
        # repeat_for_remaining_samples(sample_names, repeat_msg='Repeat for the remaining cultures:')
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def evaporative_seal(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map["location"]
        specification = parameter_value_map["specification"]

        # Get destination container type
        container_spec = record.document.find(location.container_type)
        container_class = (
            ContainerOntology.uri + "#" + container_spec.queryString.split(":")[-1]
        )
        container_str = ContainerOntology.get_term_by_uri(container_class)

        text = f"Cover `{location.name}` samples in {container_str} with your choice of material to prevent evaporation."
        execution.markdown_steps += [text]

    def unseal(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map["location"]

        # Get destination container type
        container_spec = record.document.find(location.container_type)
        container_class = (
            ContainerOntology.uri + "#" + container_spec.queryString.split(":")[-1]
        )
        container_str = ContainerOntology.get_term_by_uri(container_class)

        text = f"Remove the seal from {container_str} containing `{location.name}` samples."
        execution.markdown_steps += [text]

    def pool_samples(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        source = parameter_value_map["source"]
        samples = parameter_value_map["samples"]
        destination = parameter_value_map["destination"]
        volume = parameter_value_map["volume"]
        source_contents = read_sample_contents(source)

        # Get destination container type
        container_spec = record.document.find(destination.container_type)
        container_class = (
            ContainerOntology.uri + "#" + container_spec.queryString.split(":")[-1]
        )
        container_str = ContainerOntology.get_term_by_uri(container_class)

        # Condense replicates
        n_samples = len(source_contents)
        source_contents = list(
            dict.fromkeys(source_contents.values())
        )  # Remove replicates while preserving order, see Stack Overflow #53657523

        source_contents += source_contents  # This is a kludge to support the iGEM protocol, necessary because we don't have a good way to track replicates
        n_replicates = int(n_samples / len(source_contents))
        samples.initial_contents = write_sample_contents(source_contents)
        samples.name = source.name

        text = f"Pool {measurement_to_text(volume)} from each of {n_replicates} replicate `{source.name}` samples into {container_str} `{container_spec.name}`."
        execution.markdown_steps += [text]

    def quick_spin(self, record: ActivityNodeExecution, execution: ProtocolExecution):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        location = parameter_value_map["location"]

        # Get destination container type
        container_spec = record.document.find(location.container_type)
        container_class = (
            ContainerOntology.uri + "#" + container_spec.queryString.split(":")[-1]
        )
        container_str = ContainerOntology.get_term_by_uri(container_class)

        text = f"Perform a brief centrifugation on {container_str} containing `{container_spec.name}` samples."
        text = add_description(record, text)
        execution.markdown_steps += [text]

    def subprotocol_specialization(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        pass

    def embedded_image(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()

        image = parameter_value_map["image"]
        caption = parameter_value_map["caption"]

        text = f'\n\n![]({image})\n<p align="center">{caption}</p>\n'

        execution.markdown_steps[-1] += text

    def culture_plates(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        container = parameter_value_map["specification"]
        quantity = parameter_value_map["quantity"]
        growth_medium = parameter_value_map["growth_medium"]
        samples = parameter_value_map["samples"]

        # Get destination container type
        container_uri = (
            ContainerOntology.uri + "#" + container.queryString.split(":")[-1]
        )
        container_str = ContainerOntology.get_term_by_uri(container_uri)
        samples.name = container.name

        execution.markdown_steps += [
            f"Obtain {quantity} x {container_str} containing {growth_medium.name} growth medium for culturing `{samples.name}`"
        ]

    def pick_colonies(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        colonies = parameter_value_map["colonies"]
        quantity = parameter_value_map["quantity"]
        replicates = parameter_value_map["replicates"]
        samples = parameter_value_map["samples"]

        # Copy input SampleArray properties to output
        # TODO: maybe this should be abstracted out into a convenience method
        samples.initial_contents = colonies.initial_contents
        samples.name = colonies.name
        samples.format = colonies.format
        execution.markdown_steps += [
            f"Pick {replicates} colonies from each `{colonies.name}` plate."
        ]

    def excel_metadata(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        filename = parameter_value_map["filename"]
        for_samples = parameter_value_map["for_samples"]
        metadata = parameter_value_map["metadata"]
        df = pd.read_excel(filename, index_col=0, header=0)
        x = xr.Dataset.from_dataframe(df)
        metadata.descriptions = json.dumps(x.to_dict())
        metadata.for_samples = for_samples

    def join_metadata(
        self, record: ActivityNodeExecution, execution: ProtocolExecution
    ):
        call = record.call.lookup()
        parameter_value_map = call.parameter_value_map()
        metadata = parameter_value_map["metadata"]
        dataset = parameter_value_map["dataset"]
        enhanced_dataset = parameter_value_map["enhanced_dataset"]

    def dataset_to_text(self, dataset: Dataset):
        # Assumes that the data file is the same name as the markdown file, aside from the extension
        if self.out_file:
            xlsx_file = self.out_file.split(".")[0] + ".xlsx"
        else:
            xlsx_file = (
                "template.xlsx"  # Dummy value used when generating, but not writing md
            )
        return f"Dataset: [{xlsx_file}]({xlsx_file})"


def measurement_to_text(measure: sbol3.Measure):
    measurement_scalar = measure.value
    measurement_units = tyto.OM.get_term_by_uri(measure.unit)
    return f"{measurement_scalar} {measurement_units}"


def get_sample_names(
    inputs: Union[SampleArray, sbol3.Component], error_msg, coordinates=None
) -> List[str]:
    # Since some behavior inputs may be specified as either a SampleArray or directly as a list
    # of Components, this provides a convenient way to unpack a list of sample names
    input_names = []
    if isinstance(inputs, SampleArray):
        if inputs.initial_contents:
            initial_contents = read_sample_contents(inputs)
            if coordinates:
                input_names = {inputs.document.find(initial_contents[coordinates]).name}
            else:
                input_names = {
                    inputs.document.find(c).name
                    for c in initial_contents.values()
                    if c is not None
                }
    elif isinstance(inputs, Iterable):
        input_names = {i.name for i in inputs}
    else:
        input_names = {inputs.name}
    if not all([name is not None for name in input_names]):
        raise ValueError(error_msg)
    return sorted(input_names)


def repeat_for_remaining_samples(names: List[str], repeat_msg: str):
    # Helps convert multiple samples to natural language
    if len(names) == 1:
        return ""
    elif len(names) == 2:
        return f"{repeat_msg} {names[1]}"
    elif len(names) == 3:
        return f"{repeat_msg} {names[1]} and {names[2]}"
    else:
        remaining = ", ".join([f"`{name}`" for name in names[1:-1]])
        remaining += f", and `{names[-1]}`"
        return f" {repeat_msg} {remaining}."


def get_sample_label(sample: SampleCollection, record: ActivityNodeExecution) -> str:
    # Lookup sample container to get the container name, and use that
    # as the sample label
    if isinstance(sample, SampleMask):
        sample = sample.source.lookup()
    return record.document.find(sample.container_type).name


def write_sample_contents(
    sample_array: Union[dict, List[sbol3.Component]], replicates=1
) -> str:
    if isinstance(sample_array, SampleArray):
        old_contents = read_sample_contents(sample_array)
        initial_contents = []
        for r in range(replicates):
            for c in old_contents.values():
                initial_contents.append(c)
                # sample_array.document.find(c).name += f' replicate {r}'
        initial_contents = {i + 1: c for i, c in enumerate(initial_contents)}
    else:
        initial_contents = {
            i + 1: c for i, c in enumerate(sample_array) for r in range(replicates)
        }
    return quote(json.dumps(initial_contents))


def read_sample_contents(sample_array: Union[sbol3.Component, SampleArray]) -> dict:
    if not isinstance(sample_array, SampleArray):
        return {"1": sample_array.identity}
    if sample_array.initial_contents == "https://github.com/synbiodex/pysbol3#missing":
        return {}
    if not sample_array.initial_contents:
        return {}
    # De-serialize the initial_contents field of a SampleArray
    contents = deserialize_sample_format(sample_array.initial_contents, sample_array)
    if isinstance(contents, xr.DataArray):
        contents = contents[Strings.SAMPLE].data.tolist()
    return contents


def add_description(record, text):
    description = record.node.lookup().description
    if description:
        text += f" {description}"
    return text
