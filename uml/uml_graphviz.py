import html

import sbol3
import tyto


def _gv_sanitize(id: str):
    return html.escape(id.replace(":", "_"))


def identified_dot_label(self, parent_identity=None):
    truncated = _gv_sanitize(
        self.identity.replace(f"{parent_identity.lookup().namespace}", "")
    )
    in_struct = "_".join(truncated.split("/", 1)).replace("/", ":")
    return in_struct


sbol3.Identified.dot_label = identified_dot_label  # Add to class via monkey patch


def measure_str(self):
    if self.unit.startswith("http://www.ontology-of-units-of-measure.org"):
        unit = tyto.OM.get_term_by_uri(self.unit)
    else:
        unit = self.unit.rsplit("/", maxsplit=1)[1]
    return f"{self.value} {unit}"


sbol3.Measure.__str__ = measure_str


def identified_str(self):
    return str(self.name or self.display_id)


sbol3.Identified.__str__ = identified_str
