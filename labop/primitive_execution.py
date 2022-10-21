import json
import types
from urllib.parse import quote, unquote
import logging

import xarray as xr
import sbol3

import labop
from labop_convert.plate_coordinates import coordinate_rect_to_row_col_pairs, get_aliquot_list, num2row
import uml

from typing import List, Dict

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)

PRIMITIVE_BASE_NAMESPACE = "https://bioprotocols.org/labop/primitives/"

def call_behavior_execution_compute_output(self, parameter, sample_format):
    """
    Get parameter value from call behavior execution
    :param self:
    :param parameter: output parameter to define value
    :return: value
    """
    primitive = self.node.lookup().behavior.lookup()
    call = self.call.lookup()
    inputs = [x for x in call.parameter_values if x.parameter.lookup().property_value.direction == uml.PARAMETER_IN]
    value = primitive.compute_output(inputs, parameter, sample_format)
    return value
labop.CallBehaviorExecution.compute_output = call_behavior_execution_compute_output

def call_behavior_action_compute_output(self, inputs, parameter, sample_format):
    """
    Get parameter value from call behavior action
    :param self:
    :param inputs: token values for object pins
    :param parameter: output parameter to define value
    :return: value
    """
    primitive = self.behavior.lookup()
    inputs = self.input_parameter_values(inputs=inputs)
    value = primitive.compute_output(inputs, parameter, sample_format)
    return value
uml.CallBehaviorAction.compute_output = call_behavior_action_compute_output

def call_behavior_action_input_parameter_values(self, inputs=None):
    """
    Get parameter values for all inputs
    :param self:
    :param parameter: output parameter to define value
    :return: value
    """

    # Get the parameter values from input tokens for input pins
    input_pin_values = {}
    if inputs:
        input_pin_values = {token.token_source.lookup().node.lookup().identity:
                                    uml.literal(token.value, reference=True)
                            for token in inputs if not token.edge}


    # Get Input value pins
    value_pin_values = {pin.identity: pin.value for pin in self.inputs if hasattr(pin, "value")}
    # Convert References
    value_pin_values = {k: (uml.LiteralReference(value=self.document.find(v.value))
                            if hasattr(v, "value") and
                               (isinstance(v.value, sbol3.refobj_property.ReferencedURI) or
                                isinstance(v, uml.LiteralReference))
                            else  uml.LiteralReference(value=v))
                        for k, v in value_pin_values.items()}
    pin_values = { **input_pin_values, **value_pin_values} # merge the dicts

    parameter_values = [labop.ParameterValue(parameter=self.pin_parameter(pin.name).property_value,
                                            value=pin_values[pin.identity])
                        for pin in self.inputs if pin.identity in pin_values]
    return parameter_values
uml.CallBehaviorAction.input_parameter_values = call_behavior_action_input_parameter_values

def resolve_value(v):
        if not isinstance(v, uml.LiteralReference):
            return v.value
        else:
            resolved = v.value.lookup()
            if isinstance(resolved, uml.LiteralSpecification):
                return resolved.value
            else:
                return resolved

def input_parameter_map(inputs: List[labop.ParameterValue]):
    map = {}
    for input in inputs:
        i_parameter = input.parameter.lookup().property_value
        value = input.value.get_value()
        map[i_parameter.name] = value
    return map

def empty_container_compute_output(self, inputs, parameter, sample_format):
    if parameter.name == "samples" and \
       parameter.type == 'http://bioprotocols.org/labop#SampleArray':
        # Make a SampleArray
        input_map = input_parameter_map(inputs)
        spec = input_map["specification"]
        contents = self.initialize_contents(sample_format)
        name = f"{parameter.name}"
        sample_array = labop.SampleArray(name=name,
                                   container_type=spec,
                                   contents=contents)
        # This attribute isn't formally specified in the ontology yet, but supports handling of different sample formats by BehaviorSpecialiations
        sample_array.format = sample_format
        return sample_array
    else:
        return None

def plate_coordinates_compute_output(self, inputs, parameter, sample_format):
    if parameter.name == "samples" and \
    parameter.type == 'http://bioprotocols.org/labop#SampleCollection':
        input_map = input_parameter_map(inputs)
        source = input_map["source"]
        coordinates = input_map["coordinates"]
        # convert coordinates into a boolean sample mask array
        # 1. read source contents into array
        # 2. create parallel array for entries noted in coordinates
        mask_array = source.mask(coordinates)
        mask = labop.SampleMask(source=source,
                                mask=mask_array)
        return mask

def measure_absorbance_compute_output(self, inputs, parameter, sample_format):
    if parameter.name == "measurements" and \
       parameter.type == 'http://bioprotocols.org/labop#SampleData':
        input_map = input_parameter_map(inputs)
        samples = input_map["samples"]
        sample_data = labop.SampleData(from_samples=samples)
        return sample_data

primitive_to_output_function = {
    "EmptyContainer" : empty_container_compute_output,
    "PlateCoordinates" : plate_coordinates_compute_output,
    "MeasureAbsorbance": measure_absorbance_compute_output
}

def initialize_primitive_compute_output(doc: sbol3.Document):
    for k, v in primitive_to_output_function.items():
        try:
            p = labop.get_primitive(doc, k)
            p.compute_output = types.MethodType(v, p)
        except Exception as e:
            l.warn(f"Could not set compute_output() for primitive {k}, did you import the correct library?")



def primitive_compute_output(self, inputs, parameter, sample_format):
    """
    Compute the value for parameter given the inputs. This default function will be overridden for specific primitives.
    :param self:
    :param inputs: list of labop.ParameterValue
    :param parameter: Parameter needing value
    :return: value
    """
    if hasattr(parameter, 'type') and parameter.type in sbol3.Document._uri_type_map:
        # Generalized handler for output tokens, see #125
        # TODO: This currently assumes the output token is an sbol3.TopLevel
        # Still needs special handling for non-toplevel tokens

        builder_fxn = sbol3.Document._uri_type_map[parameter.type]

        # Construct object with a unique URI
        instance_count = 0
        successful = False
        while not successful:
            try:
                token_id = f'{parameter.name}{instance_count}'
                output_token = builder_fxn(token_id, type_uri=parameter.type)
                if isinstance(output_token, sbol3.TopLevel):
                    self.document.add(output_token)
                else:
                    output_token = builder_fxn(None, type_uri=parameter.type)
                successful = True
            except ValueError:
                instance_count += 1
        return output_token
    else:
        l.warning(f'No builder found for output Parameter of {parameter.name}. Returning a string literal by default.')
        return f"{parameter.name}"
labop.Primitive.compute_output = primitive_compute_output

def empty_container_initialize_contents(self, sample_format):
    if self.identity == 'https://bioprotocols.org/labop/primitives/sample_arrays/EmptyContainer':
        # FIXME need to find a definition of the container topology from the type
        # FIXME this assumes a 96 well plate

        l.warn("Warning: Assuming that the SampleArray is a 96 well microplate!")
        aliquots = get_aliquot_list(geometry="A1:H12")
        #contents = json.dumps(xr.DataArray(dims=("aliquot", "contents"),
        #                                   coords={"aliquot": aliquots}).to_dict())
        if sample_format == 'xarray':
            contents = json.dumps(xr.DataArray(aliquots, dims=("aliquot")).to_dict())
        elif sample_format == 'json':
            contents = quote(json.dumps({}))
    else:
        raise Exception(f"Cannot initialize contents of: {self.identity}")
    return contents
labop.Primitive.initialize_contents = empty_container_initialize_contents

def declare_primitive(
    document: sbol3.Document,
    library: str,
    primitive_name: str,
    template: labop.Primitive = None,
    inputs: List[Dict] = {},
    outputs: List[Dict] = {},
    description: str = ""
):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE + library)
    try:
        primitive = labop.get_primitive(
            name=primitive_name, doc=document
        )
        if not primitive:
            raise Exception("Need to create the primitive")
    except Exception as e:
        primitive = labop.Primitive(primitive_name)
        primitive.description = description
        if template:
            primitive.inherit_parameters(template)
        for input in inputs:
            optional = input['optional'] if 'optional' in  input else False
            default_value = input['default_value'] if 'default_value' in input else None
            primitive.add_input(input['name'], input['type'], optional=optional, default_value=None)
        for output in outputs:
            primitive.add_output(output['name'], output['type'])

        document.add(primitive)
    sbol3.set_namespace(old_ns)
    return primitive