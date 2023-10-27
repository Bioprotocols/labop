import sbol3
import tyto

import labop
from labop.execution.harness import ProtocolHarness, ProtocolSpecialization
from labop.strings import Strings
from labop_convert.markdown.markdown_specialization import MarkdownSpecialization


def generate_protocol(doc, protocol: labop.Protocol) -> labop.Protocol:
    from labop.constants import rpm

    doc.add(rpm)
    #############################################
    # Create the protocols

    print("Constructing measurement sub-protocols")
    # This will be used 10 times generating "OD_Plate_1" .. "OD_Plate_9"

    split_and_measure = labop.Protocol(
        "SplitAndMeasure", name="Split samples, dilute, and measure"
    )
    split_and_measure.description = """
    Subprotocol to split a portion of each sample in a plate into another plate, diluting
    with PBS, then measure OD and fluorescence from that other plate
    """
    doc.add(split_and_measure)

    # plate for split-and-measure subroutine
    od_plate = labop.Container(
        name="OD Plate", type=tyto.NCIT.Microplate, max_coordinate="H12"
    )
    split_and_measure.locations = {od_plate}

    # Inputs: collection of samples, pbs_source
    samples = split_and_measure.add_input(
        name="samples",
        description="Samples to measure",
        type="http://bioprotocols.org/labop#LocatedSamples",
    )
    pbs_source = split_and_measure.add_input(
        name="pbs",
        description="Source for PBS",
        type="http://bioprotocols.org/labop#LocatedSamples",
    )

    # subprotocol steps
    s_p = split_and_measure.execute_primitive(
        "Dispense",
        source=pbs_source,
        destination=od_plate,
        amount=sbol3.Measure(90, tyto.OM.microliter),
    )
    split_and_measure.add_flow(
        split_and_measure.initial(), s_p
    )  # dispensing OD can be a first action
    s_u = split_and_measure.execute_primitive("Unseal", location=samples)
    split_and_measure.add_flow(
        split_and_measure.initial(), s_u
    )  # unsealing the growth plate can be a first action
    s_t = split_and_measure.execute_primitive(
        "TransferInto",
        source=samples,
        destination=s_p.output_pin("samples"),
        amount=sbol3.Measure(10, tyto.OM.microliter),
        mixCycles=sbol3.Measure(10, tyto.OM.number),
    )
    split_and_measure.add_flow(
        s_u, s_t
    )  # transfer can't happen until growth plate is unsealed

    # add the measurements, in parallel
    ready_to_measure = labop.Fork()
    split_and_measure.activities.append(ready_to_measure)
    split_and_measure.add_flow(s_t.output_pin("samples"), ready_to_measure)
    measurement_complete = labop.Join()
    split_and_measure.activities.append(measurement_complete)

    s_a = split_and_measure.execute_primitive(
        "MeasureAbsorbance",
        samples=ready_to_measure,
        wavelength=sbol3.Measure(600, tyto.OM.nanometer),
        numFlashes=sbol3.Measure(25, tyto.OM.number),
    )
    v_a = split_and_measure.add_output("absorbance", s_a.output_pin("measurements"))
    split_and_measure.add_flow(v_a, measurement_complete)

    gains = {0.1, 0.2, 0.16}
    for g in gains:
        s_f = split_and_measure.execute_primitive(
            "MeasureFluorescence",
            samples=ready_to_measure,
            excitationWavelength=sbol3.Measure(488, tyto.OM.nanometer),
            emissionBandpassWavelength=sbol3.Measure(530, tyto.OM.nanometer),
            numFlashes=sbol3.Measure(25, tyto.OM.number),
            gain=sbol3.Measure(g, tyto.OM.number),
        )
        v_f = split_and_measure.add_output(
            "fluorescence_" + str(g), s_f.output_pin("measurements")
        )
        split_and_measure.add_flow(v_f, measurement_complete)

    s_c = split_and_measure.execute_primitive("Cover", location=od_plate)
    split_and_measure.add_flow(measurement_complete, s_c)
    split_and_measure.add_flow(s_c, split_and_measure.final())

    s_s = split_and_measure.execute_primitive(
        "Seal", location=samples, type="http://autoprotocol.org/lids/breathable"
    )  # need to turn this into a proper ontology
    split_and_measure.add_flow(measurement_complete, s_s)
    split_and_measure.add_flow(s_s, split_and_measure.final())

    print("Measurement sub-protocol construction complete")

    overnight_od_measure = labop.Protocol(
        "OvernightODMeasure", name="Split samples and measure, without dilution"
    )
    overnight_od_measure.description = """
    Subprotocol to split a portion of each sample in an unsealed plate into another plate, then measure OD and fluorescence from that other plate
    """
    doc.add(overnight_od_measure)

    # plate for split-and-measure subroutine
    od_plate = labop.Container(
        name="OD Plate", type=tyto.NCIT.Microplate, max_coordinate="H12"
    )
    overnight_od_measure.locations = {od_plate}

    # Input: collection of samples
    samples = overnight_od_measure.add_input(
        name="samples",
        description="Samples to measure",
        type="http://bioprotocols.org/labop#LocatedSamples",
    )

    # subprotocol steps
    s_t = overnight_od_measure.execute_primitive(
        "Transfer",
        source=samples,
        destination=od_plate,
        amount=sbol3.Measure(200, tyto.OM.microliter),
    )
    overnight_od_measure.add_flow(overnight_od_measure.initial(), s_t)  # first action

    # add the measurements, in parallel
    ready_to_measure = labop.Fork()
    overnight_od_measure.activities.append(ready_to_measure)
    overnight_od_measure.add_flow(s_t.output_pin("samples"), ready_to_measure)
    measurement_complete = labop.Join()
    overnight_od_measure.activities.append(measurement_complete)

    s_a = overnight_od_measure.execute_primitive(
        "MeasureAbsorbance",
        samples=ready_to_measure,
        wavelength=sbol3.Measure(600, tyto.OM.nanometer),
        numFlashes=sbol3.Measure(25, tyto.OM.number),
    )
    v_a = overnight_od_measure.add_output("absorbance", s_a.output_pin("measurements"))
    overnight_od_measure.add_flow(v_a, measurement_complete)

    gains = {0.1, 0.2, 0.16}
    for g in gains:
        s_f = overnight_od_measure.execute_primitive(
            "MeasureFluorescence",
            samples=ready_to_measure,
            excitationWavelength=sbol3.Measure(488, tyto.OM.nanometer),
            emissionBandpassWavelength=sbol3.Measure(530, tyto.OM.nanometer),
            numFlashes=sbol3.Measure(25, tyto.OM.number),
            gain=sbol3.Measure(g, tyto.OM.number),
        )
        v_f = overnight_od_measure.add_output(
            "fluorescence_" + str(g), s_f.output_pin("measurements")
        )
        overnight_od_measure.add_flow(v_f, measurement_complete)

    s_c = overnight_od_measure.execute_primitive("Cover", location=od_plate)
    overnight_od_measure.add_flow(measurement_complete, s_c)
    overnight_od_measure.add_flow(s_c, overnight_od_measure.final())

    overnight_od_measure.add_flow(measurement_complete, overnight_od_measure.final())

    print("Overnight measurement sub-protocol construction complete")
    #############################################
    # Now the full protocol

    print("Making protocol")

    activity = labop.Protocol("GrowthCurve", name="SD2 Yeast growth curve protocol")
    activity.description = """
    Protocol from SD2 Yeast States working group for studying growth curves:
    Grow up cells and read with plate reader at n-hour intervals
    """
    doc.add(activity)

    # Create the materials to be provisioned
    PBS = sbol3.Component("PBS", "https://identifiers.org/pubchem.compound:24978514")
    PBS.name = (
        "Phosphate-Buffered Saline"  # I'd like to get this name from PubChem with tyto
    )
    doc.add(PBS)
    # need to retrieve and convert this one
    SC_media = sbol3.Component("SC_Media", "TBD", name="Synthetic Complete Media")
    doc.add(SC_media)
    SC_plus_dox = sbol3.Component(
        "SC_Media_plus_dox",
        "TBD",
        name="Synthetic Complete Media plus 40nM Doxycycline",
    )
    doc.add(SC_plus_dox)
    activity.material += {PBS, SC_media, SC_plus_dox}

    ## create the containers
    # provisioning sources
    pbs_source = labop.Container(name="PBS Source", type=tyto.NCIT.Bottle)
    sc_source = labop.Container(
        name="SC Media + 40nM Doxycycline Source", type=tyto.NCIT.Bottle
    )
    om_source = labop.Container(name="Overnight SC Media Source", type=tyto.NCIT.Bottle)
    # plates for the general protocol
    overnight_plate = labop.Container(
        name="Overnight Growth Plate",
        type=tyto.NCIT.Microplate,
        max_coordinate="H12",
    )
    overnight_od_plate = labop.Container(
        name="Overnight Growth Plate",
        type=tyto.NCIT.Microplate,
        max_coordinate="H12",
    )
    growth_plate = labop.Container(
        name="Growth Curve Plate",
        type=tyto.NCIT.Microplate,
        max_coordinate="H12",
    )
    activity.locations = {
        pbs_source,
        sc_source,
        om_source,
        overnight_plate,
        growth_plate,
    }

    # One input: a microplate full of strains
    # TODO: change this to allow alternative places
    strain_plate = activity.add_input(
        name="strain_plate",
        description="Plate of strains to grow",
        type="http://bioprotocols.org/labop#LocatedSamples",
    )
    # input_plate = labop.Container(name='497943_4_UWBF_to_stratoes', type=tyto.NCIT.Microplate, max_coordinate='H12')

    print("Constructing protocol steps")

    # set up the sources
    p_pbs = activity.execute_primitive(
        "Provision",
        resource=PBS,
        destination=pbs_source,
        amount=sbol3.Measure(117760, tyto.OM.microliter),
    )
    activity.add_flow(activity.initial(), p_pbs)  # start with provisioning
    p_om = activity.execute_primitive(
        "Provision",
        resource=SC_media,
        destination=om_source,
        amount=sbol3.Measure(98, tyto.OM.milliliter),
    )
    activity.add_flow(activity.initial(), p_om)  # start with provisioning
    p_scm = activity.execute_primitive(
        "Provision",
        resource=SC_plus_dox,
        destination=sc_source,
        amount=sbol3.Measure(117200, tyto.OM.microliter),
    )
    activity.add_flow(activity.initial(), p_scm)  # start with provisioning

    # prep the overnight culture, then seal away the source plate again
    s_d = activity.execute_primitive(
        "Dispense",
        source=p_om.output_pin("samples"),
        destination=overnight_plate,
        amount=sbol3.Measure(500, tyto.OM.microliter),
    )
    s_u = activity.execute_primitive("Unseal", location=strain_plate)
    s_t = activity.execute_primitive(
        "TransferInto",
        source=strain_plate,
        destination=s_d.output_pin("samples"),
        amount=sbol3.Measure(5, tyto.OM.microliter),
        mixCycles=sbol3.Measure(10, tyto.OM.number),
    )
    s_s = activity.execute_primitive(
        "Seal",
        location=strain_plate,
        type="http://autoprotocol.org/lids/breathable",
    )  # need to turn this into a proper ontology
    activity.add_flow(
        s_u, s_t
    )  # transfer can't happen until strain plate is unsealed ...
    activity.add_flow(s_t, s_s)  # ... and must complete before we re-seal it

    # run the overnight culture
    overnight_samples = s_t.output_pin("samples")
    s_s = activity.execute_primitive(
        "Seal",
        location=overnight_samples,
        type="http://autoprotocol.org/lids/breathable",
    )  # need to turn this into a proper ontology
    s_i = activity.execute_primitive(
        "Incubate",
        location=overnight_samples,
        temperature=sbol3.Measure(30, tyto.OM.get_uri_by_term("degree Celsius")),
        duration=sbol3.Measure(16, tyto.OM.hour),
        shakingFrequency=sbol3.Measure(350, rpm.identity),
    )
    activity.add_flow(s_t, s_s)  # sealing after transfer
    activity.add_flow(s_s, s_i)  # incubation after sealing

    # Check the OD after running overnight; note that this is NOT the same measurement process as for the during-growth measurements
    s_u = activity.execute_primitive(
        "Unseal", location=overnight_samples
    )  # added because using the subprotocol leaves a sealed plate
    activity.add_flow(s_i, s_u)  # growth plate after measurement
    s_m = activity.execute_subprotocol(overnight_od_measure, samples=overnight_samples)
    activity.add_flow(s_u, s_m)  # measurement after incubation and unsealing

    # Set up the growth plate
    s_d = activity.execute_primitive(
        "Dispense",
        source=p_scm.output_pin("samples"),
        destination=growth_plate,
        amount=sbol3.Measure(700, tyto.OM.microliter),
    )
    s_t = activity.execute_primitive(
        doc.find("TransferInto"),
        source=overnight_samples,
        destination=s_d.output_pin("samples"),
        amount=sbol3.Measure(2, tyto.OM.microliter),
        mixCycles=sbol3.Measure(10, tyto.OM.number),
    )
    s_s = activity.execute_primitive(
        "Seal",
        location=overnight_samples,
        type="http://autoprotocol.org/lids/breathable",
    )  # need to turn this into a proper ontology
    activity.add_flow(
        s_u, s_t
    )  # transfer can't happen until overnight plate is unsealed ...
    activity.add_flow(s_t, s_s)  # ... and must complete before we re-seal it
    activity.add_flow(s_m, s_s)  # ... as must its measurement

    # run the step-by-step culture
    growth_samples = s_t.output_pin("samples")
    last_round = None
    # sample_hours = [1, 3, 6, 9, 12, 15, 18, 21, 24]   # Original: modified to be friendly to human execution
    sample_hours = [1, 3, 6, 9, 18, 21, 24]
    for i in range(0, len(sample_hours)):
        incubation_hours = sample_hours[i] - (sample_hours[i - 1] if i > 0 else 0)
        s_i = activity.execute_primitive(
            "Incubate",
            location=growth_samples,
            temperature=sbol3.Measure(30, tyto.OM.get_uri_by_term("degree Celsius")),
            duration=sbol3.Measure(incubation_hours, tyto.OM.hour),
            shakingFrequency=sbol3.Measure(350, rpm.identity),
        )
        s_m = activity.execute_subprotocol(
            split_and_measure,
            samples=growth_samples,
            pbs=p_pbs.output_pin("samples"),
        )
        if last_round:
            activity.add_flow(last_round, s_i)  # measurement after incubation
        activity.add_flow(s_i, s_m)  # measurement after incubation
        last_round = s_m

    activity.add_flow(last_round, activity.final())

    print("Protocol construction complete")

    ######################
    # Invocation of protocol on a plate:;

    # plate for invoking the protocol
    # input_plate = labop.Container(name='497943_4_UWBF_to_stratoes', type=tyto.NCIT.Microplate, max_coordinate='H12')

    print("Validating document")
    for e in doc.validate().errors:
        print(e)
    for w in doc.validate().warnings:
        print(w)

    print("Writing document")

    doc.write("test/testfiles/growth_curve.json", "json-ld")
    doc.write("test/testfiles/growth_curve.ttl", "turtle")

    print("Complete")


if __name__ == "__main__":
    harness = ProtocolHarness(
        entry_point=generate_protocol,
        artifacts=[
            ProtocolSpecialization(
                specialization=MarkdownSpecialization(
                    "test_golden_gate_markdown.md",
                    sample_format=Strings.XARRAY,
                )
            )
        ],
        namespace="https://labop.io/examples/protocols/golden-gate-assembly/",
        protocol_name="GoldenGate_assembly",
        protocol_long_name="Golden Gate Assembly",
        protocol_version="1.0",
        protocol_description="""
    This protocol is for Golden Gate Assembly of pairs of DNA fragments into plasmids using the New England Biolabs
    Golden Gate Assembly Kit (BsaI-HFv2), product ID NEB #E1601.
    Protocol implements the specific case of two part assembly for the NEB-provided protocol:
    https://www.neb.com/protocols/2018/10/02/golden-gate-assembly-protocol-for-using-neb-golden-gate-assembly-mix-e1601
    """,
    )
    harness.run()
