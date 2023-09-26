import json

import rdflib as rdfl
import sbol3

CONT_NS = rdfl.Namespace("https://sift.net/container-ontology/container-ontology#")
OM_NS = rdfl.Namespace("http://www.ontology-of-units-of-measure.org/resource/om-2/")

PREFIX_MAP = json.dumps({"cont": CONT_NS, "om": OM_NS})


ddh2o = sbol3.Component("ddH2O", "https://identifiers.org/pubchem.substance:24901740")
ddh2o.name = "Water, sterile-filtered, BioReagent, suitable for cell culture"

ludox = sbol3.Component("LUDOX", "https://identifiers.org/pubchem.substance:24866361")
ludox.name = "LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O"
