"""
The Parameter class defines the functions corresponding to the dynamically generated labop class Parameter
"""


import uml.inner as inner

from .utils import labop_hash


class Parameter(inner.Parameter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __hash__(self):
        return labop_hash(self.identity)

    def __str__(self):
        """
        Create a human readable string for a parameter.
        :param self:
        :return: str
        """
        default_value_str = f"= {self.default_value}" if self.default_value else ""
        return f"""{self.name}: {self.type} {default_value_str}"""

    def template(self):
        """
        Create a template for a parameter. Used for populating UI elements.
        :param self:
        :return: str
        """
        default_value_str = f"= {self.default_value}" if self.default_value else ""
        return f"""{self.name}=\'{default_value_str}\'"""
