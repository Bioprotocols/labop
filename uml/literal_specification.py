"""
The LiteralSpecification class defines the functions corresponding to the dynamically generated labop class LiteralSpecification.
"""

import html

from . import inner
from .value_specification import ValueSpecification


class LiteralSpecification(inner.LiteralSpecification, ValueSpecification):
    def __init__(self, *args, **kwargs):
        r"""
        Create a LiteralSpecification

        Examples:
            >>> my_literal_specification = LiteralSpecification()
        """
        super().__init__(*args, **kwargs)

    def get_value(self):
        r"""
        Get value of the LiteralSpecification.

        Examples:
            >>> my_literal_specification.get_value()
            Traceback (most recent call last):
            ...
            TypeError: <class '__main__.LiteralSpecification'> is abstract and does not have a value.  Try instantiating a subclass instead.
            >>> from uml.literal_boolean import LiteralBoolean
            >>> LiteralBoolean(value=False).get_value()
            False

        Returns
        -------
        type
            The value of the literal whose type is determined by the subclass of LiteralSpecification.
        """
        if type(self) == LiteralSpecification:
            raise TypeError(
                f"{__class__} is abstract and does not have a value.  Try instantiating a subclass instead."
            )
        return self.value

    def __str__(self):
        r"""
        Generate string representation of LiteralSpecification

        Examples:
            >>> str(my_literal_specification)
            Traceback (most recent call last):
            ...
            TypeError: <class '__main__.LiteralSpecification'> is abstract and does not have a value.  Try instantiating a subclass instead.
            >>> from uml.literal_boolean import LiteralBoolean
            >>> str(LiteralBoolean(value=False))
            'False'

        Returns
        -------
        str
            HTML-compatible string representation of the LiteralSpecification.
        """
        value = self.get_value()
        if isinstance(value, str) or isinstance(value, int) or isinstance(value, bool):
            val_str = html.escape(str(value)).lstrip("\n").replace("\n", "<br/>")
        else:
            val_str = str(value)
        return val_str


if __name__ == "__main__":
    import doctest

    doctest.testmod(extraglobs={"my_literal_specification": LiteralSpecification()})
