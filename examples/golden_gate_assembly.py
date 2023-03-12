import os
import tempfile
import unittest
import filecmp
import sbol3
import labop
import tyto


# import labop_md
import uml

#############################################
# set up the document
print("Setting up document")
doc = sbol3.Document()
sbol3.set_namespace("https://bbn.com/scratch/")

#############################################
# Import the primitive libraries
print("Importing libraries")
labop.import_library("liquid_handling")
print("... Imported liquid handling")
labop.import_library("plate_handling")
print("... Imported plate handling")
labop.import_library("spectrophotometry")
print("... Imported spectrophotometry")
labop.import_library("sample_arrays")
print("... Imported sample arrays")

#############################################
# Create the protocol
print("Creating protocol")
protocol = labop.Protocol("GoldenGate_assembly")
protocol.name = "Golden Gate Assembly"
protocol.description = """
This protocol is for Golden Gate Assembly of pairs of DNA fragments into plasmids using the New England Biolabs
Golden Gate Assembly Kit (BsaI-HFv2), product ID NEB #E1601.
Protocol implements the specific case of two part assembly for the NEB-provided protocol:
https://www.neb.com/protocols/2018/10/02/golden-gate-assembly-protocol-for-using-neb-golden-gate-assembly-mix-e1601
"""
doc.add(protocol)

# create the materials to be provisioned
nf_h2o = sbol3.Component(
    "nuclease_free_H2O", "https://identifiers.org/pubchem.compound:962"
)
nf_h2o.name = "Nuclease-free Water"
doc.add(nf_h2o)

gg_buf = sbol3.Component("NEB_GoldenGate_Buffer", tyto.SBO.functional_entity)
gg_buf.name = "NEB T4 DNA Ligase Buffer (10X)"
gg_buf.derived_from.append(
    "https://www.neb.com/products/e1601-neb-golden-gate-assembly-mix"
)
doc.add(gg_buf)

gg_mix = sbol3.Component("NEB_GoldenGate_AssemblyMix", tyto.SBO.functional_entity)
gg_mix.name = "NEB Golden Gate Assembly Mix"
gg_mix.derived_from.append(
    "https://www.neb.com/products/e1601-neb-golden-gate-assembly-mix"
)
doc.add(gg_mix)

# add an parameters for specifying the layout of the DNA source plate and build plate
dna_sources = protocol.input_value(
    "source_samples", "http://bioprotocols.org/labop#SampleCollection"
)
# TODO: add_input should be returning a usable ActivityNode!
dna_build_layout = protocol.input_value(
    "build_layout", "http://bioprotocols.org/labop#SampleData"
)

# actual steps of the protocol
# get a plate space for building
build_wells = protocol.primitive_step("DuplicateCollection", source=dna_build_layout)

# put DNA into the selected wells following the build plan
protocol.primitive_step(
    "TransferByMap",
    source=dna_sources,
    destination=build_wells.output_pin("samples"),
    plan=dna_build_layout,
)

# put buffer, assembly mix, and water into build wells too
protocol.primitive_step(
    "Provision",
    resource=gg_buf,
    destination=build_wells.output_pin("samples"),
    amount=sbol3.Measure(2, tyto.OM.microliter),
)
protocol.primitive_step(
    "Provision",
    resource=gg_mix,
    destination=build_wells.output_pin("samples"),
    amount=sbol3.Measure(1, tyto.OM.microliter),
)
protocol.primitive_step(
    "Provision",
    resource=nf_h2o,
    destination=build_wells.output_pin("samples"),
    amount=sbol3.Measure(15, tyto.OM.microliter),
)

# seal and spin to mix
protocol.primitive_step(
    "Seal", location=build_wells.output_pin("samples")
)  # TODO: add type
protocol.primitive_step(
    "Spin",
    acceleration=sbol3.Measure(
        300, "http://bioprotocols.org/temporary/unit/g"
    ),  # TODO: replace with OM-2 unit on resolution of https://github.com/HajoRijgersberg/OM/issues/54
    duration=sbol3.Measure(3, tyto.OM.minute),
)
protocol.primitive_step("Unseal", location=build_wells.output_pin("samples"))

# incubation steps
protocol.primitive_step(
    "Incubate",
    location=build_wells.output_pin("samples"),
    duration=sbol3.Measure(60, tyto.OM.minute),
    temperature=sbol3.Measure(37, tyto.OM.get_uri_by_term("degree Celsius")),
)  # TODO: replace after resolution of https://github.com/SynBioDex/tyto/issues/29
protocol.primitive_step(
    "Incubate",
    location=build_wells.output_pin("samples"),
    duration=sbol3.Measure(5, tyto.OM.minute),
    temperature=sbol3.Measure(60, tyto.OM.get_uri_by_term("degree Celsius")),
)  # TODO: replace after resolution of https://github.com/SynBioDex/tyto/issues/29


output = protocol.designate_output(
    "constructs",
    "http://bioprotocols.org/labop#SampleCollection",
    build_wells.output_pin("samples"),
)
protocol.order(
    protocol.get_last_step(), output
)  # don't return until all else is complete


########################################
# Validate and write the document
print("Validating and writing protocol")
v = doc.validate()
assert len(v) == 0, "".join(f"\n {e}" for e in v)

temp_name = os.path.join(tempfile.gettempdir(), "golden_gate_assembly.nt")
doc.write(temp_name, sbol3.SORTED_NTRIPLES)
print(f"Wrote file as {temp_name}")

# render and view the dot
dot = protocol.to_dot()
dot.render(f"{protocol.name}.gv")
dot.view()
