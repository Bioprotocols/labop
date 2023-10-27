"""
The LiteralReference class defines the functions corresponding to the dynamically generated labop class LiteralReference
"""
import sbol3
import tyto

from . import inner
from .literal_specification import LiteralSpecification


class LiteralReference(inner.LiteralReference, LiteralSpecification):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_value(self: inner.LiteralReference):
        return self.value.lookup()

    def dot_value(self):
        literal = self.value.lookup()
        if isinstance(literal, sbol3.Measure):
            # TODO: replace kludge with something nicer
            if literal.unit.startswith("http://www.ontology-of-units-of-measure.org"):
                unit = tyto.OM.get_term_by_uri(literal.unit)
            else:
                unit = literal.unit.rsplit("/", maxsplit=1)[1]
            val_str = f"{literal.value} {unit}"
        else:
            val_str = literal.name or literal.display_id
        return val_str
