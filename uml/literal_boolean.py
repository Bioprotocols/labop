"""
The LiteralBoolean class defines the functions corresponding to the dynamically generated labop class LiteralBoolean
"""

from . import inner
from .literal_specification import LiteralSpecification


class LiteralBoolean(inner.LiteralBoolean, LiteralSpecification):
    def __init__(self, *args, **kwargs):
        r"""
        Create a Boolean valued literal

        Examples:
            >>> my_boolean = LiteralBoolean(value=True)
            >>> my_boolean.get_value()
            True
        """
        super().__init__(*args, **kwargs)

    def dot_value(self) -> str:
        r"""
        Return string representation that can be rendered by Graphviz dot.

        Examples:
            >>> my_boolean.dot_value()
            'True'

        Returns
        -------
        str
            String representing the LiteralBoolean
        """
        return str(self.value)


if __name__ == "__main__":
    import doctest

    doctest.testmod(extraglobs={"my_boolean": LiteralBoolean(value=True)})
