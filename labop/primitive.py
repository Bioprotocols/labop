"""
The Primitive class defines the functions corresponding to the dynamically generated labop class Primitive
"""

import logging
from typing import Dict, List

import sbol3

from uml import PARAMETER_IN, PARAMETER_OUT, Behavior, inner_to_outer

from . import inner
from .library import loaded_libraries

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
        self,
        inputs,
        parameter,
        sample_format,
        call_behavior_execution_hash,
        engine,
    ):
        """
        Compute the value for parameter given the inputs. This default function will be overridden for specific primitives.
        :param self:
        :param inputs: list of ParameterValue
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

    def auto_advance(self) -> bool:
        return super(Behavior).auto_advance() or (
            not hasattr(self.compute_output, "__func__")
            or self.compute_output.__func__ != Primitive.compute_output
        )
