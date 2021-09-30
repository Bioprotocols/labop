from paml import Protocol, Primitive
import uml

def protocol_template():
    """
    Create a template instantiation of a protocol.  Used for populating UI elements.
    :param
    :return: str
    """
    return f"protocol = paml.Protocol(\n\t\"Identity\",\n\tname=\"Name\",\n\tdescription=\"Description\")"
Protocol.template = protocol_template

def primitive_template(self):
    """
    Create a template instantiation of a primitive for writing a protocol.  Used for populating UI elements.
    :param self:
    :return: str
    """
    args = ",\n\t".join([f"{parameter.property_value.template()}"
                            for parameter in self.parameters
                            if parameter.property_value.direction == uml.PARAMETER_IN])
    return f"step = protocol.primitive_step(\n\t\'{self.display_id}\',\n\t{args}\n\t)"
Primitive.template = primitive_template
