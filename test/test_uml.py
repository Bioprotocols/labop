import unittest

import sbol3

from uml import (
    Behavior,
    Constraint,
    LiteralInteger,
    LiteralNull,
    OrderedPropertyValue,
    Parameter,
)


class TestUML(unittest.TestCase):
    def test_ordered_properties(self):
        property = LiteralNull()
        ordered_property = OrderedPropertyValue(index=0, property_value=property)
        assert (
            ordered_property.property_value == property and ordered_property.index == 0
        )

    def test_ordered_constraint(self):
        property1 = OrderedPropertyValue(
            index=0, property_value=LiteralInteger(value=0)
        )
        property2 = OrderedPropertyValue(
            index=1, property_value=LiteralInteger(value=2)
        )
        constraint = Constraint(constrained_elements=[property1, property2])
        assert (
            property1 in constraint.constrained_elements
            and property2 in constraint.constrained_elements
        )

    def test_ordered_behavior_parameters(self):
        doc = sbol3.Document()
        sbol3.set_namespace("https://bbn.com/scratch/")

        parameter1 = OrderedPropertyValue(
            index=0,
            property_value=Parameter(
                direction="in",
                default_value=LiteralInteger(value=0),
                is_unique=True,
                is_ordered=True,
                lower_value=LiteralInteger(value=0),
                upper_value=LiteralInteger(value=10),
            ),
        )
        parameter2 = OrderedPropertyValue(
            index=1,
            property_value=Parameter(
                direction="in",
                default_value=LiteralInteger(value=0),
                is_unique=True,
                is_ordered=True,
                lower_value=LiteralInteger(value=0),
                upper_value=LiteralInteger(value=10),
            ),
        )
        behavior = Behavior("b", parameters=[parameter1, parameter2])
        assert parameter1 in behavior.parameters and parameter2 in behavior.parameters

        doc.add(behavior)
        v = doc.validate()
        assert not v.errors and not v.warnings, "".join(
            str(e) for e in doc.validate().errors
        )
