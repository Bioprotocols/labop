"""
The SampleCollection class defines the functions corresponding to the dynamically generated labop class SampleCollection
"""

from . import inner


class SampleCollection(inner.SampleCollection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


if __name__ == "__main__":
    import doctest

    doctest.testmod(
        # extraglobs={"my_literal_specification": LiteralSpecification()}
    )
