import json

import rdflib as rdfl
import sbol3
import tyto

CONT_NS = rdfl.Namespace("https://sift.net/container-ontology/container-ontology#")
OM_NS = rdfl.Namespace("http://www.ontology-of-units-of-measure.org/resource/om-2/")

PREFIX_MAP = json.dumps({"cont": CONT_NS, "om": OM_NS})


ddh2o = sbol3.Component("ddH2O", "https://identifiers.org/pubchem.substance:24901740")
ddh2o.name = "Water, sterile-filtered, BioReagent, suitable for cell culture"

ludox = sbol3.Component("LUDOX", "https://identifiers.org/pubchem.substance:24866361")
ludox.name = "LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O"

pbs = sbol3.Component("pbs", "https://pubchem.ncbi.nlm.nih.gov/compound/24978514")
pbs.name = "Phosphate Buffered Saline"

silica_beads = sbol3.Component(
    "silica_beads",
    "https://nanocym.com/wp-content/uploads/2018/07/NanoCym-All-Datasheets-.pdf",
)
silica_beads.name = "NanoCym 950 nm monodisperse silica nanoparticles"
silica_beads.description = "3e9 NanoCym microspheres"

fluorescein = sbol3.Component(
    "fluorescein", "https://pubchem.ncbi.nlm.nih.gov/substance/329753341"
)
fluorescein.name = "Fluorescein"

cascade_blue = sbol3.Component(
    "cascade_blue", "https://pubchem.ncbi.nlm.nih.gov/substance/57269662"
)
cascade_blue.name = "Cascade Blue"

sulforhodamine = sbol3.Component(
    "sulforhodamine", "https://pubchem.ncbi.nlm.nih.gov/compound/139216224"
)
sulforhodamine.name = "Sulforhodamine"

rpm = sbol3.UnitDivision(
    "rpm",
    name="rpm",
    symbol="rpm",
    label="revolutions per minute",
    numerator=tyto.OM.revolution,
    denominator=tyto.OM.minute,
)
