"""
The Primitive class defines the functions corresponding to the dynamically generated labop class Primitive
"""

import logging
import types
from typing import Dict, List

import sbol3

from uml import PARAMETER_IN, PARAMETER_OUT, Behavior, inner_to_outer

from . import inner
from .dataset import Dataset
from .lab_interface import LabInterface
from .library import loaded_libraries
from .sample_array import SampleArray
from .sample_data import SampleData
from .sample_mask import SampleMask
from .sample_metadata import SampleMetadata
from .utils.helpers import get_short_uuid

PRIMITIVE_BASE_NAMESPACE = "https://bioprotocols.org/labop/primitives/"


l = logging.Logger(__file__)
l.setLevel(logging.INFO)


class Primitive(inner.Primitive, Behavior):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def inherit_parameters(self, parent_primitive):
        """Add the parameters from parent_primitive to self parameters

        :param parent_primitive: Primitive with parameters to inherit
        """
        for p in parent_primitive.parameters:
            param = p.property_value
            if param.direction == PARAMETER_IN:
                self.add_input(
                    param.name,
                    param.type,
                    optional=(param.lower_value.value == 0),
                    default_value=param.default_value,
                )
            elif param.direction == PARAMETER_OUT:
                self.add_output(param.name, param.type)
            else:
                raise Exception(f"Cannot inherit parameter {param.name}")

    def get_primitive(doc: sbol3.Document, name: str, copy_to_doc: bool = True):
        """Get a Primitive for use in the protocol, either already in the document or imported from a linked library

        :param doc: Working document
        :param name: Name of primitive, either displayId or full URI
        :return: Primitive that has been found
        """
        found = doc.find(name)
        if not found:
            found = {
                n: l.find(name) for (n, l) in loaded_libraries.items() if l.find(name)
            }
            if len(found) >= 2:
                raise ValueError(
                    f'Ambiguous primitive: found "{name}" in multiple libraries: {found.keys()}'
                )
            if len(found) == 0:
                raise ValueError(f'Could not find primitive "{name}" in any library')
            found = next(iter(found.values()))
            if copy_to_doc:
                found = found.copy(doc)

        # Convert inner class to outer class
        try:
            found.__class__ = inner_to_outer(found, package="labop")
        except:
            raise ValueError(
                f'"{name}" should be a Primitive, but it resolves to a {type(found).__name__}'
            )
        return found

    def __str__(self):
        """
        Create a human readable string describing the Primitive
        :param self:
        :return: str
        """

        def mark_optional(parameter):
            return (
                ""
                if not parameter.lower_value
                else "(Optional) "
                if parameter.lower_value.value < 1
                else ""
            )

        input_parameter_strs = "\n\t".join(
            [
                f"{parameter.property_value}{mark_optional(parameter.property_value)}"
                for parameter in self.parameters
                if parameter.property_value.direction == PARAMETER_IN
            ]
        )
        input_str = (
            f"Input Parameters:\n\t{input_parameter_strs}"
            if len(input_parameter_strs) > 0
            else ""
        )
        output_parameter_strs = "\n\t".join(
            [
                f"{parameter.property_value}{mark_optional(parameter.property_value)}"
                for parameter in self.parameters
                if parameter.property_value.direction == PARAMETER_OUT
            ]
        )
        output_str = (
            f"Output Parameters:\n\t{output_parameter_strs}"
            if len(output_parameter_strs) > 0
            else ""
        )
        return f"""
    Primitive: {self.identity}
    '''
    {self.description}
    '''
    {input_str}
    {output_str}
                """

    def compute_output(
        self, inputs, parameter, sample_format, call_behavior_execution_hash
    ):
        """
        Compute the value for parameter given the inputs. This default function will be overridden for specific primitives.
        :param self:
        :param inputs: list of labop.ParameterValue
        :param parameter: Parameter needing value
        :return: value
        """
        if (
            hasattr(parameter, "type")
            and parameter.type in sbol3.Document._uri_type_map
        ):
            # Generalized handler for output tokens, see #125
            # TODO: This currently assumes the output token is an sbol3.TopLevel
            # Still needs special handling for non-toplevel tokens

            builder_fxn = sbol3.Document._uri_type_map[parameter.type]

            # Construct object with a unique URI
            instance_count = 0
            successful = False
            while not successful:
                try:
                    token_id = f"{parameter.name}{instance_count}"
                    output_token = builder_fxn(token_id, type_uri=parameter.type)
                    if isinstance(output_token, sbol3.TopLevel):
                        self.document.add(output_token)
                    else:
                        output_token = builder_fxn(None, type_uri=parameter.type)
                    successful = True
                except ValueError:
                    instance_count += 1

            # Convert the inner class into an outer class
            try:
                output_token.__class__ = inner_to_outer(output_token, package="labop")
            except Exception as e:
                pass

            return output_token
        else:
            l.warning(
                f"No builder found for output Parameter of {parameter.name}. Returning a string literal by default."
            )
            return f"{parameter.name}"

    def transfer_out(self, source, target, plan, sample_format):
        if sample_format == "xarray":
            sourceResult, targetResult = self.transfer(
                source, target, plan, sample_format
            )
            return sourceResult
        else:
            raise Exception(f"Cannot initialize contents of: {self.identity}")

    def transfer_in(self, source, target, plan, sample_format):
        if sample_format == "xarray":
            sourceResult, targetResult = self.transfer(
                source, target, plan, sample_format
            )
            return targetResult
        else:
            raise Exception(f"Cannot initialize contents of: {self.identity}")

    def transfer(self, source, target, plan, sample_format):
        if sample_format == "xarray":
            source_contents = source.to_data_array()
            target_contents = target.to_data_array()
            transfer = plan.get_map()
            if (
                source.name in transfer.source_array
                and target.name in transfer.target_array
            ):
                source_result = source_contents.rename(
                    {"aliquot": "source_aliquot", "array": "source_array"}
                )
                target_result = target_contents.rename(
                    {"aliquot": "target_aliquot", "array": "target_array"}
                )
                source_concentration = source_result / source_result.sum(dim="contents")

                amount_transferred = source_concentration * transfer

                source_result = source_result - amount_transferred.sum(
                    dim=["target_aliquot", "target_array"]
                )
                target_result = target_result + amount_transferred.sum(
                    dim=["source_aliquot", "source_array"]
                )

                return source_result, target_result
            else:
                return source_contents, target_contents
        else:
            raise Exception(f"Cannot initialize contents of: {self.identity}")

    def empty_container_compute_output(
        self, input_map, parameter, sample_format, call_behavior_execution_hash
    ):
        if (
            parameter.name == "samples"
            and parameter.type == "http://bioprotocols.org/labop#SampleArray"
        ):
            # Make a SampleArray
            spec = input_map["specification"]
            sample_array = (
                input_map["sample_array"] if "sample_array" in input_map else None
            )

            if not sample_array:
                sample_array = SampleArray.from_container_spec(
                    spec, sample_format=sample_format
                )
            sample_array.name = spec.name

            # This attribute isn't formally specified in the ontology yet, but supports handling of different sample formats by BehaviorSpecialiations
            # sample_array.format = sample_format
            return sample_array
        else:
            return None

    def empty_rack_compute_output(
        self, input_map, parameter, sample_format, call_behavior_execution_hash
    ):
        if (
            parameter.name == "slots"
            and parameter.type == "http://bioprotocols.org/labop#SampleArray"
        ):
            # Make a SampleArray
            spec = input_map["specification"]
            sample_array = SampleArray.from_container_spec(
                spec, sample_format=sample_format
            )
            return sample_array
        else:
            return None

    def load_container_on_instrument_compute_output(
        self, input_map, parameter, sample_format, call_behavior_execution_hash
    ):
        if (
            parameter.name == "samples"
            and parameter.type == "http://bioprotocols.org/labop#SampleArray"
        ):
            # Make a SampleArray
            spec = input_map["specification"]
            sample_array = SampleArray.from_container_spec(
                spec, sample_format=sample_format
            )
            return sample_array
        else:
            return None

    def plate_coordinates_compute_output(
        self, input_map, parameter, sample_format, call_behavior_execution_hash
    ):
        if (
            parameter.name == "samples"
            and parameter.type == "http://bioprotocols.org/labop#SampleCollection"
        ):
            source = input_map["source"]
            coordinates = input_map["coordinates"]
            # convert coordinates into a boolean sample mask array
            # 1. read source contents into array
            # 2. create parallel array for entries noted in coordinates
            mask = SampleMask.from_coordinates(
                source, coordinates, sample_format=sample_format
            )

            return mask

    def measure_absorbance_compute_output(
        self, input_map, parameter, sample_format, call_behavior_execution_hash
    ):
        if (
            parameter.name == "measurements"
            and parameter.type == "http://bioprotocols.org/labop#Dataset"
        ):
            samples = input_map["samples"]
            wl = input_map["wavelength"]

            measurements = LabInterface.measure_absorbance(
                samples, wl.value, sample_format
            )
            name = f"{self.display_id}.{parameter.name}.{get_short_uuid(call_behavior_execution_hash+hash(parameter))}"
            sample_data = SampleData(
                name=name, from_samples=samples, values=measurements
            )
            sample_metadata = SampleMetadata.for_primitive(
                self, input_map, samples, sample_format=sample_format
            )
            sample_dataset = Dataset(data=sample_data, metadata=[sample_metadata])
            return sample_dataset

    def measure_fluorescence_compute_output(
        self, input_map, parameter, sample_format, call_behavior_execution_hash
    ):
        if (
            parameter.name == "measurements"
            and parameter.type == "http://bioprotocols.org/labop#Dataset"
        ):
            samples = input_map["samples"]
            exwl = input_map["excitationWavelength"]
            emwl = input_map["emissionWavelength"]
            bandpass = input_map["emissionBandpassWidth"]

            measurements = LabInterface.measure_fluorescence(
                samples,
                exwl.value,
                emwl.value,
                bandpass.value,
                sample_format,
            )
            name = f"{self.display_id}.{parameter.name}.{get_short_uuid(get_short_uuid(call_behavior_execution_hash+hash(parameter)))}"
            sample_data = SampleData(
                name=name, from_samples=samples, values=measurements
            )
            sample_metadata = SampleMetadata.for_primitive(
                self, input_map, samples, sample_format=sample_format
            )
            sample_dataset = Dataset(data=sample_data, metadata=[sample_metadata])
            return sample_dataset

    def join_metadata_compute_output(
        self, input_map, parameter, sample_format, call_behavior_execution_hash
    ):
        if (
            parameter.name == "enhanced_dataset"
            and parameter.type == "http://bioprotocols.org/labop#Dataset"
        ):
            dataset = input_map["dataset"]
            metadata = input_map["metadata"]
            enhanced_dataset = Dataset(dataset=[dataset], linked_metadata=[metadata])
            return enhanced_dataset

    def join_datasets_compute_output(
        self, input_map, parameter, sample_format, call_behavior_execution_hash
    ):
        if (
            parameter.name == "joint_dataset"
            and parameter.type == "http://bioprotocols.org/labop#Dataset"
        ):
            datasets = input_map["dataset"]
            metadata = (
                input_map["metadata"]
                if "metadata" in input_map and input_map["metadata"]
                else []
            )
            joint_dataset = Dataset(dataset=datasets, linked_metadata=metadata)
            return joint_dataset

    def excel_metadata_compute_output(
        self, input_map, parameter, sample_format, call_behavior_execution_hash
    ):
        if (
            parameter.name == "metadata"
            and parameter.type == "http://bioprotocols.org/labop#SampleMetadata"
        ):
            filename = input_map["filename"]
            for_samples = input_map["for_samples"]  # check dataarray
            metadata = SampleMetadata.from_excel(
                filename, for_samples, sample_format=sample_format
            )
            return metadata

    def compute_metadata_compute_output(
        self, input_map, parameter, sample_format, call_behavior_execution_hash
    ):
        if (
            parameter.name == "metadata"
            and parameter.type == "http://bioprotocols.org/labop#SampleMetadata"
        ):
            for_samples = input_map["for_samples"]
            metadata = labop.SampleMetadata.from_sample_graph(for_samples, engine)
            return metadata

    def transfer_by_map_compute_output(
        self,
        inputs,
        parameter,
        sample_format,
    ):
        if (
            parameter.name == "sourceResult"
            and parameter.type == "http://bioprotocols.org/labop#SampleCollection"
        ):
            source = input_map["source"]
            target = input_map["destination"]
            plan = input_map["plan"]
            spec = source.container_type
            contents = self.transfer_out(source, target, plan, sample_format)
            name = f"{parameter.name}"
            result = labop.SampleArray(
                name=name, container_type=spec, contents=contents
            )
        elif (
            parameter.name == "destinationResult"
            and parameter.type == "http://bioprotocols.org/labop#SampleCollection"
        ):
            input_map = input_parameter_map(inputs)
            source = input_map["source"]
            target = input_map["destination"]
            plan = input_map["plan"]
            spec = source.container_type
            contents = self.transfer_in(source, target, plan, sample_format)
            name = f"{parameter.name}"
            result = labop.SampleArray(
                name=name, container_type=spec, contents=contents
            )
        return result

    primitive_to_output_function = {
        "EmptyContainer": empty_container_compute_output,
        "PlateCoordinates": plate_coordinates_compute_output,
        "MeasureAbsorbance": measure_absorbance_compute_output,
        "MeasureFluorescence": measure_fluorescence_compute_output,
        "EmptyInstrument": empty_rack_compute_output,
        "EmptyRack": empty_rack_compute_output,
        "LoadContainerOnInstrument": load_container_on_instrument_compute_output,
        "JoinMetadata": join_metadata_compute_output,
        "JoinDatasets": join_datasets_compute_output,
        "ExcelMetadata": excel_metadata_compute_output,
        "ComputeMetadata": compute_metadata_compute_output,
    }

    def initialize_primitive_compute_output(doc: sbol3.Document):
        for k, v in Primitive.primitive_to_output_function.items():
            try:
                p = Primitive.get_primitive(doc, k, copy_to_doc=False)
                p.compute_output = types.MethodType(v, p)
            except Exception as e:
                l.warning(
                    f"Could not set compute_output() for primitive {k}, did you import the correct library?"
                )

    def declare_primitive(
        document: sbol3.Document,
        library: str,
        primitive_name: str,
        template=None,
        inputs: List[Dict] = {},
        outputs: List[Dict] = {},
        description: str = "",
    ):
        old_ns = sbol3.get_namespace()
        sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE + library)
        try:
            primitive = Primitive.get_primitive(name=primitive_name, doc=document)
            if not primitive:
                raise Exception("Need to create the primitive")
        except Exception as e:
            primitive = Primitive.Primitive(primitive_name)
            primitive.description = description
            if template:
                primitive.inherit_parameters(template)
            for input in inputs:
                optional = input["optional"] if "optional" in input else False
                default_value = (
                    input["default_value"] if "default_value" in input else None
                )
                primitive.add_input(
                    input["name"],
                    input["type"],
                    optional=optional,
                    default_value=None,
                )
            for output in outputs:
                primitive.add_output(output["name"], output["type"])

            document.add(primitive)
        sbol3.set_namespace(old_ns)
        return primitive

    def template(self):
        """
        Create a template instantiation of a primitive for writing a protocol.  Used for populating UI elements.
        :param self:
        :return: str
        """
        args = ",\n\t".join(
            [
                f"{parameter.property_value.template()}"
                for parameter in self.parameters
                if parameter.property_value.direction == PARAMETER_IN
            ]
        )
        return f"step = protocol.primitive_step(\n\t'{self.display_id}',\n\t{args}\n\t)"
