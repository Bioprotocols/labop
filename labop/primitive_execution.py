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
        if 'sample_array' in input_map:
            sample_array = input_map["sample_array"]
        else:
            spec = input_map["specification"]
            initial_contents = self.initialize_contents(sample_format)
            name = f"{parameter.name}"
            sample_array = labop.SampleArray(name=name,
                                    container_type=spec,
                                    initial_contents=initial_contents)
            # This attribute isn't formally specified in the ontology yet, but supports handling of different sample formats by BehaviorSpecialiations
            sample_array.format = sample_format
        return sample_array
    else:
        return None

def empty_rack_compute_output(self, inputs, parameter, sample_format):
    if parameter.name == "slots" and \
       parameter.type == 'http://bioprotocols.org/labop#SampleArray':
        # Make a SampleArray
        input_map = input_parameter_map(inputs)
        spec = input_map["specification"]
        if spec.queryString == 'cont:Opentrons24TubeRackwithEppendorf1.5mLSafe-LockSnapcap':
            geometry = 'A1:C8'
        else:
            geometry = 'A1:H12'
        initial_contents = self.initialize_contents(sample_format, geometry)
        name = f"{parameter.name}"
        sample_array = labop.SampleArray(name=name,
                                   container_type=spec,
                                   initial_contents=initial_contents)
        # This attribute isn't formally specified in the ontology yet, but supports handling of different sample formats by BehaviorSpecialiations
        sample_array.format = sample_format
        return sample_array
    else:
        return None

def empty_rack_compute_output(self, inputs, parameter, sample_format):
    if parameter.name == "slots" and \
       parameter.type == 'http://bioprotocols.org/labop#SampleArray':
        # Make a SampleArray
        input_map = input_parameter_map(inputs)
        spec = input_map["specification"]
        if spec.queryString == 'cont:Opentrons24TubeRackwithEppendorf1.5mLSafe-LockSnapcap':
            geometry = 'A1:C8'
        else:
            geometry = 'A1:H12'
        initial_contents = self.initialize_contents(sample_format, geometry)
        name = f"{parameter.name}"
        sample_array = labop.SampleArray(name=name,
                                   container_type=spec,
                                   initial_contents=initial_contents)
        # This attribute isn't formally specified in the ontology yet, but supports handling of different sample formats by BehaviorSpecialiations
        sample_array.format = sample_format
        return sample_array
    else:
        return None

def load_container_on_instrument_compute_output(self, inputs, parameter, sample_format):
    if parameter.name == "samples" and \
       parameter.type == 'http://bioprotocols.org/labop#SampleArray':
        # Make a SampleArray
        input_map = input_parameter_map(inputs)
        spec = input_map["specification"]
        # TODO: handle different containers, e.g. 8-tube strips, 12-tube strips
        initial_contents = self.initialize_contents(sample_format)
        name = f"{parameter.name}"
        sample_array = labop.SampleArray(name=name,
                                   container_type=spec,
                                   initial_contents=initial_contents)
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

        if sample_format == 'xarray':
            data = json.dumps(samples.initialize_dataset("absorbance").to_dict())
        elif sample_format == 'json':
            data = quote(json.dumps({k: None for k, v in json.loads(unquote(input_map["samples"].initial_contents)).items()}))
        else:
            raise Exception(f"Cannot initialize contents of: {self.identity}")

        sample_data = labop.SampleData(from_samples=samples, values=data)
        return sample_data

def transfer_by_map_compute_output(self, inputs, parameter, sample_format):
    if parameter.name == "sourceResult" and \
       parameter.type == 'http://bioprotocols.org/labop#SampleCollection':
        input_map = input_parameter_map(inputs)
        source = input_map["source"]
        target = input_map["destination"]
        plan  = input_map["plan"]
        spec = source.container_type
        initial_contents = self.transfer_out(source, target, plan, sample_format)
        name = f"{parameter.name}"
        result = labop.SampleArray(name=name,
                                   container_type=spec,
                                   initial_contents=initial_contents)
    elif parameter.name == "destinationResult" and \
         parameter.type == 'http://bioprotocols.org/labop#SampleCollection':
        input_map = input_parameter_map(inputs)
        source = input_map["source"]
        target = input_map["destination"]
        plan  = input_map["plan"]
        spec = source.container_type
        initial_contents = self.transfer_in(source, target, plan, sample_format)
        name = f"{parameter.name}"
        result = labop.SampleArray(name=name,
                                   container_type=spec,
                                   initial_contents=initial_contents)
    return result


primitive_to_output_function = {
    "EmptyContainer" : empty_container_compute_output,
    "PlateCoordinates" : plate_coordinates_compute_output,
    "MeasureAbsorbance": measure_absorbance_compute_output,
    "EmptyInstrument": empty_rack_compute_output,
    "EmptyRack": empty_rack_compute_output,
    "LoadContainerOnInstrument": load_container_on_instrument_compute_output,
    "TransferByMap": transfer_by_map_compute_output,
}

def initialize_primitive_compute_output(doc: sbol3.Document):
    for k, v in primitive_to_output_function.items():
        try:
            p = labop.get_primitive(doc, k, copy_to_doc=False)
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

def empty_container_initialize_contents(self, sample_format, geometry='A1:H12'):

    aliquots = get_aliquot_list(geometry)
    if sample_format == 'xarray':
        initial_contents = json.dumps(xr.DataArray(aliquots, dims=("aliquot")).to_dict())
    elif sample_format == 'json':
        initial_contents = quote(json.dumps({c: None for c in aliquots}))
    else:
        raise Exception(f"Cannot initialize contents of: {self.identity}")
    return initial_contents
labop.Primitive.initialize_contents = empty_container_initialize_contents

def transfer_out(self, source, target, plan, sample_format):
    if sample_format == 'xarray':
        sourceResult, targetResult = self.transfer(source, target, plan, sample_format)
        return json.dumps(sourceResult.to_dict())
    elif sample_format == 'json':
        contents = quote(json.dumps({c: None for c in aliquots}))
    else:
        raise Exception(f"Cannot initialize contents of: {self.identity}")
    return contents
labop.Primitive.transfer_out = transfer_out

def transfer_in(self, source, target, plan, sample_format):
    if sample_format == 'xarray':
        sourceResult, targetResult = self.transfer(source, target, plan, sample_format)
        return json.dumps(targetResult.to_dict())
    elif sample_format == 'json':
        contents = quote(json.dumps({c: None for c in aliquots}))
    else:
        raise Exception(f"Cannot initialize contents of: {self.identity}")
    return contents
labop.Primitive.transfer_in = transfer_in

def transfer(self, source, target, plan, sample_format):
    if sample_format == 'xarray':
        source_contents = source.to_data_array()
        target_contents = target.to_data_array()
        transfer = plan.get_map()
        if source.name in transfer.source_array and target.name in transfer.target_array:
            source_result = source_contents.rename({"aliquot": "source_aliquot", "array": "source_array"})
            target_result = target_contents.rename({"aliquot": "target_aliquot", "array": "target_array"})
            source_concentration = source_result / source_result.sum(dim="contents")

            amount_transferred = source_concentration * transfer

            source_result = source_result - amount_transferred.sum(dim=["target_aliquot", "target_array"])
            target_result = target_result + amount_transferred.sum(dim=["source_aliquot", "source_array"])

            return source_result, target_result
        else:
            return source_contents, target_contents

    elif sample_format == 'json':
        contents = quote(json.dumps({c: None for c in aliquots}))
    else:
        raise Exception(f"Cannot initialize contents of: {self.identity}")
    return contents
labop.Primitive.transfer = transfer

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
