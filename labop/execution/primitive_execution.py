import logging

from ..dataset import Dataset
from ..sample_array import SampleArray
from ..sample_data import SampleData
from ..sample_mask import SampleMask
from ..sample_metadata import SampleMetadata
from ..utils.helpers import get_short_uuid

PRIMITIVE_BASE_NAMESPACE = "https://bioprotocols.org/labop/primitives/"


l = logging.Logger(__file__)
l.setLevel(logging.INFO)


def transfer_out(self, source, target, plan, sample_format):
    if sample_format == "xarray":
        sourceResult, targetResult = self.transfer(source, target, plan, sample_format)
        return sourceResult
    else:
        raise Exception(f"Cannot initialize contents of: {self.identity}")


def transfer_in(self, source, target, plan, sample_format):
    if sample_format == "xarray":
        sourceResult, targetResult = self.transfer(source, target, plan, sample_format)
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
    self, input_map, parameter, sample_format, call_behavior_execution_hash, engine
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
    self, input_map, parameter, sample_format, call_behavior_execution_hash, engine
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
    self, input_map, parameter, sample_format, call_behavior_execution_hash, engine
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
    self, input_map, parameter, sample_format, call_behavior_execution_hash, engine
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
    self, input_map, parameter, sample_format, call_behavior_execution_hash, engine
):
    if (
        parameter.name == "measurements"
        and parameter.type == "http://bioprotocols.org/labop#Dataset"
    ):
        samples = input_map["samples"]
        wl = input_map["wavelength"]
        from labop.execution.lab_interface import LabInterface

        measurements = LabInterface.measure_absorbance(samples, wl.value, sample_format)
        name = f"{self.display_id}.{parameter.name}.{get_short_uuid(call_behavior_execution_hash+hash(parameter))}"
        sample_data = SampleData(name=name, from_samples=samples, values=measurements)
        sample_metadata = SampleMetadata.for_primitive(
            self, input_map, samples, sample_format=sample_format
        )
        sample_dataset = Dataset(data=sample_data, metadata=[sample_metadata])
        return sample_dataset


def measure_fluorescence_compute_output(
    self, input_map, parameter, sample_format, call_behavior_execution_hash, engine
):
    if (
        parameter.name == "measurements"
        and parameter.type == "http://bioprotocols.org/labop#Dataset"
    ):
        samples = input_map["samples"]
        exwl = input_map["excitationWavelength"]
        emwl = input_map["emissionWavelength"]
        bandpass = input_map["emissionBandpassWidth"]
        from labop.execution.lab_interface import LabInterface

        measurements = LabInterface.measure_fluorescence(
            samples,
            exwl.value,
            emwl.value,
            bandpass.value,
            sample_format,
        )
        name = f"{self.display_id}.{parameter.name}.{get_short_uuid(get_short_uuid(call_behavior_execution_hash+hash(parameter)))}"
        sample_data = SampleData(name=name, from_samples=samples, values=measurements)
        sample_metadata = SampleMetadata.for_primitive(
            self, input_map, samples, sample_format=sample_format
        )
        sample_dataset = Dataset(data=sample_data, metadata=[sample_metadata])
        return sample_dataset


def join_metadata_compute_output(
    self, input_map, parameter, sample_format, call_behavior_execution_hash, engine
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
    self, input_map, parameter, sample_format, call_behavior_execution_hash, engine
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
    self, input_map, parameter, sample_format, call_behavior_execution_hash, engine
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
    self, input_map, parameter, sample_format, call_behavior_execution_hash, engine
):
    if (
        parameter.name == "metadata"
        and parameter.type == "http://bioprotocols.org/labop#SampleMetadata"
    ):
        for_samples = input_map["for_samples"]
        metadata = SampleMetadata.from_sample_graph(for_samples, engine)
        return metadata


def transfer_by_map_compute_output(self, inputs, parameter, sample_format, engine):
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
        result = SampleArray(name=name, container_type=spec, contents=contents)
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
        result = SampleArray(name=name, container_type=spec, contents=contents)
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
