import json
import paml
from paml_convert.plate_coordinates import coordinate_rect_to_row_col_pairs, num2col
import uml
import xarray as xr
import logging


l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


def call_behavior_execution_compute_output(self, parameter):
    """
    Get parameter value from call behavior execution
    :param self:
    :param parameter: output parameter to define value
    :return: value
    """
    primitive = self.node.lookup().behavior.lookup()
    call = self.call.lookup()
    inputs = [x for x in call.parameter_values if x.parameter.lookup().property_value.direction == uml.PARAMETER_IN]
    value = primitive.compute_output(inputs, parameter)
    return value
paml.CallBehaviorExecution.compute_output = call_behavior_execution_compute_output

def primitive_compute_output(self, inputs, parameter):
    """
    Compute the value for parameter given the inputs. This default function will be overridden for specific primitives.
    :param self:
    :param inputs: list of paml.ParameterValue
    :param parameter: Parameter needing value
    :return: value
    """

    l.debug(f"Computing the output of primitive: {self.identity}, parameter: {parameter.name}")

    if self.identity == 'https://bioprotocols.org/paml/primitives/sample_arrays/EmptyContainer' and \
        parameter.name == "samples" and \
        parameter.type == 'http://bioprotocols.org/paml#SampleArray':
        # Make a SampleArray
        for input in inputs:
            i_parameter = input.parameter.lookup().property_value
            value = input.value
            if i_parameter.name == "specification":
                spec = value.value.lookup().value if isinstance(value, uml.LiteralReference) else value.value
        contents = self.initialize_contents()
        name = f"{parameter.name}"
        sample_array = paml.SampleArray(name=name,
                                   container_type=spec,
                                   contents=contents)
        return sample_array
    elif self.identity == 'https://bioprotocols.org/paml/primitives/sample_arrays/PlateCoordinates' and \
        parameter.name == "samples" and \
        parameter.type == 'http://bioprotocols.org/paml#SampleCollection':
        for input in inputs:
            i_parameter = input.parameter.lookup().property_value
            value = input.value
            if i_parameter.name == "source":
                source = value.value.lookup() if isinstance(value, uml.LiteralReference) else value.value
            elif i_parameter.name == "coordinates":
                coordinates = value.value.lookup().value if isinstance(value, uml.LiteralReference) else value.value
                # convert coordinates into a boolean sample mask array
                # 1. read source contents into array
                # 2. create parallel array for entries noted in coordinates
                mask_array = source.mask(coordinates)

        mask = paml.SampleMask(source=source,
                               mask=mask_array)
        return mask
    elif self.identity == 'https://bioprotocols.org/paml/primitives/spectrophotometry/MeasureAbsorbance' and \
        parameter.name == "measurements" and \
        parameter.type == 'http://bioprotocols.org/paml#SampleData':
        for input in inputs:
            i_parameter = input.parameter.lookup().property_value
            value = input.value
            if i_parameter.name == "samples":
                samples = value.value.lookup() if isinstance(value, uml.LiteralReference) else value.value

        sample_data = paml.SampleData(from_samples=samples)
        return sample_data
    else:
        return f"{parameter.name}"
paml.Primitive.compute_output = primitive_compute_output

def empty_container_initialize_contents(self):
    if self.identity == 'https://bioprotocols.org/paml/primitives/sample_arrays/EmptyContainer':
        # FIXME need to find a definition of the container topology from the type
        # FIXME this assumes a 96 well plate

        l.warn("Warning: Assuming that the SampleArray is a 96 well microplate!")

        row_col_pairs = coordinate_rect_to_row_col_pairs("A1:H12")
        aliquots = [f"{num2col(c+1)}{r+1}" for (r, c) in row_col_pairs]
        contents = json.dumps(xr.DataArray(aliquots, dims=("aliquot")).to_dict())
    else:
        raise Exception(f"Cannot initialize contents of: {self.identity}")
    return contents
paml.Primitive.initialize_contents = empty_container_initialize_contents
