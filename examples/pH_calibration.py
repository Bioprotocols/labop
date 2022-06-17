import json
import logging
import os
from typing import Tuple

import rdflib as rdfl
import sbol3
import tyto
from sbol3 import Document

import paml
import uml

logger: logging.Logger = logging.Logger("pH_calibration")

CONT_NS = rdfl.Namespace('https://sift.net/container-ontology/container-ontology#')
OM_NS = rdfl.Namespace('http://www.ontology-of-units-of-measure.org/resource/om-2/')


def prepare_document() -> Document:
    logger.info('Setting up document')
    doc = sbol3.Document()
    sbol3.set_namespace('https://bbn.com/scratch/')
    return doc


def import_paml_libraries() -> None:
    logger.info('Importing libraries')
    paml.import_library('liquid_handling')
    logger.info('... Imported liquid handling')
    paml.import_library('plate_handling')
    logger.info('... Imported plate handling')
    paml.import_library('spectrophotometry')
    logger.info('... Imported spectrophotometry')
    paml.import_library('sample_arrays')
    logger.info('... Imported sample arrays')


DOCSTRING = 'This protocol implements a pH calibration protocol with decision nodes.'



def create_protocol() -> paml.Protocol:
    logger.info('Creating protocol')
    protocol: paml.Protocol = paml.Protocol('pH_calibration_protocol')
    protocol.name = "pH calibration protocol"
    protocol.description = DOCSTRING
    return protocol


# def create_h2o() -> sbol3.Component:
#     ddh2o = sbol3.Component('ddH2O', 'https://identifiers.org/pubchem.substance:24901740')
#     ddh2o.name = 'Water, sterile-filtered, BioReagent, suitable for cell culture'  # TODO get via tyto
#     return ddh2o


# def create_ludox() -> sbol3.Component:
#     ludox = sbol3.Component('LUDOX', 'https://identifiers.org/pubchem.substance:24866361')
#     ludox.name = 'LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O'
#     return ludox


# PLATE_SPECIFICATION = \
#     """cont:ClearPlate and
#  cont:SLAS-4-2004 and
#  (cont:wellVolume some
#     ((om:hasUnit value om:microlitre) and
#      (om:hasNumericalValue only xsd:decimal[>= "200"^^xsd:decimal])))"""

# PREFIX_MAP = json.dumps({"cont": CONT_NS, "om": OM_NS})


# def create_plate(protocol: paml.Protocol):
#     # graph: rdfl.Graph = protocol._other_rdf
#     # plate_spec_uri = \
#     #     "https://bbn.com/scratch/iGEM_LUDOX_OD_calibration_2018/container_requirement#RequiredPlate"
#     # graph.add((plate_spec_uri, CONT_NS.containerOntologyQuery, PLATE_SPECIFICATION))
#     # plate_spec = sbol3.Identified(plate_spec_uri,
#     #                               "foo", name="RequiredPlate")
#     spec = paml.ContainerSpec(queryString=PLATE_SPECIFICATION, prefixMap=PREFIX_MAP, name='plateRequirement')
#     plate = protocol.primitive_step('EmptyContainer',
#                                     specification=spec)
#     plate.name = 'calibration plate'
#     return plate


# def provision_h2o(protocol: paml.Protocol, plate, ddh2o) -> None:
#     c_ddh2o = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A1:D1')
#     protocol.primitive_step('Provision', resource=ddh2o, destination=c_ddh2o.output_pin('samples'),
#                             amount=sbol3.Measure(100, tyto.OM.microliter))


# def provision_ludox(protocol: paml.Protocol, plate, ludox) -> None:
#     c_ludox = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A2:D2')
#     protocol.primitive_step('Provision', resource=ludox, destination=c_ludox.output_pin('samples'),
#                             amount=sbol3.Measure(100, tyto.OM.microliter))


# def measure_absorbance(protocol: paml.Protocol, plate, wavelength_param):
#     c_measure = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A1:D2')
#     return protocol.primitive_step(
#         'MeasureAbsorbance',
#         samples=c_measure.output_pin('samples'),
#         wavelength=wavelength_param,
#     )

LIBRARY_NAME = 'pH_calibration'
PRIMITIVE_BASE_NAMESPACE = 'https://bioprotocols.org/paml/primitives/'

def make_pH_meter_calibrated(protocol):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE+LIBRARY_NAME)

    pH_meter_calibrated = paml.Primitive('pHMeterCalibrated')
    pH_meter_calibrated.description = 'Determine if the pH Meter is calibrated.'
    pH_meter_calibrated.add_output('return', 'http://www.w3.org/2001/XMLSchema#boolean')
    protocol.document.add(pH_meter_calibrated)

    sbol3.set_namespace(old_ns)

    def pH_meter_calibrated_compute_output(inputs, parameter):
        return uml.literal(True)
    pH_meter_calibrated.compute_output = pH_meter_calibrated_compute_output

    decision = protocol.make_decision_node(protocol.initial(), decision_input_behavior = pH_meter_calibrated)
    return decision

def make_calibrate_pH_meter(protocol):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE+LIBRARY_NAME)

    pH_meter_calibrated = paml.Primitive('calibrate_pH_meter')
    pH_meter_calibrated.description = 'Calibrate the pH meter.'
    pH_meter_calibrated.add_output('return', 'http://www.w3.org/2001/XMLSchema#boolean')
    protocol.document.add(pH_meter_calibrated)

    sbol3.set_namespace(old_ns)

    return protocol.execute_primitive('calibrate_pH_meter')

def resolve_value(v):
    if not isinstance(v, uml.LiteralReference):
        return v.value
    else:
        resolved = v.value.lookup()
        if isinstance(resolved, uml.LiteralSpecification):
            return resolved.value
        else:
            return resolved



def make_inventorise_and_confirm_materials(protocol, reaction_volume):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE+LIBRARY_NAME)

    calculate_volume = paml.Primitive('calculate_volume')
    calculate_volume.description = 'calculate_volume'
    calculate_volume.add_input('total_volume', tyto.OM.milliliter)
    calculate_volume.add_input('percentage', tyto.OM.milliliter)
    calculate_volume.add_output('volume', tyto.OM.milliliter)
    protocol.document.add(calculate_volume)


    def calculate_volume_compute_output(inputs, parameter):
        # X% weight/volume (g/mL) = (total_volume / 100) * X
        # return total_volume * percentage/100
        for input in inputs:
            i_parameter = input.parameter.lookup().property_value
            value = input.value
            if i_parameter.name == "total_volume":
                total_volume = resolve_value(value)
            elif i_parameter.name == "percentage":
                percentage = resolve_value(value)
        volume = sbol3.Measure((total_volume*percentage)/100.0, tyto.OM.milliliter)
        return uml.literal(volume)
    calculate_volume.compute_output = calculate_volume_compute_output


    sbol3.set_namespace(old_ns)

    reaction_vessel = protocol.execute_primitive('EmptyContainer', specification="reaction_vessel")
    reaction_vessel.name = 'reaction_vessel'

    phosphoric_acid = create_phosphoric_acid()
    ddh2o = create_h2o()



    # 20% weight
    provision_phosphoric_acid = protocol.execute_primitive('Provision', resource=phosphoric_acid, destination=reaction_vessel.output_pin('samples'),
                            amount=volume_phosphoric_acid.output_pin("volume"))
    volume_phosphoric_acid = protocol.execute_primitive('calculate_volume', resource=phosphoric_acid, total_volume=reaction_volume, percentage=20)

    # 80% weight
    volume_h2o = protocol.execute_primitive('calculate_volume', resource=phosphoric_acid, total_volume=reaction_volume, percentage=80)
    provision_h2o = protocol.execute_primitive('Provision', resource=ddh2o, destination=reaction_vessel.output_pin('samples'),
                            amount=volume_h2o.output_pin("volume"))

    return


def make_is_calibration_successful(protocol, primary_input_source):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE+LIBRARY_NAME)

    calibration_successful = paml.Primitive('calibrationSuccessful')
    calibration_successful.description = 'Determine if calibration worked.'
    calibration_successful.add_output('return', 'http://www.w3.org/2001/XMLSchema#boolean')
    protocol.document.add(calibration_successful)

    sbol3.set_namespace(old_ns)

    def calibration_successful_output(inputs, parameter):
        return uml.literal(True)
    calibration_successful.compute_output = calibration_successful_output

    decision = protocol.make_decision_node(primary_input_source, decision_input_behavior = calibration_successful)
    return decision

def create_phosphoric_acid() -> sbol3.Component:
    h3po4 = sbol3.Component('phosporic_acid', tyto.PubChem.get_uri_by_term("CID1004"))
    h3po4.name = 'H3PO4: Phosphoric Acid'  # TODO get via tyto
    return h3po4

def create_h2o() -> sbol3.Component:
    ddh2o = sbol3.Component('ddH2O', 'https://identifiers.org/pubchem.substance:24901740')
    ddh2o.name = 'Water, sterile-filtered, BioReagent, suitable for cell culture'  # TODO get via tyto
    return ddh2o

def make_dispense_phosphoric_acid(protocol):
    old_ns = sbol3.get_namespace()
    sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE+LIBRARY_NAME)

    calibration_successful = paml.Primitive('calibrationSuccessful')
    calibration_successful.description = 'Determine if calibration worked.'
    calibration_successful.add_output('return', 'http://www.w3.org/2001/XMLSchema#boolean')
    protocol.document.add(calibration_successful)

    sbol3.set_namespace(old_ns)

    c_ddh2o = protocol.primitive_step('PlateCoordinates', source=plate.output_pin('samples'), coordinates='A1:D1')
    protocol.primitive_step('Provision', resource=ddh2o, destination=c_ddh2o.output_pin('samples'),
                            amount=sbol3.Measure(100, tyto.OM.microliter))




def make_error_message(protocol, message):

    try:
        if not paml.get_primitive('error_message'):
            raise Exception("Need to create the primitive")
    except Exception as e:
        old_ns = sbol3.get_namespace()
        sbol3.set_namespace(PRIMITIVE_BASE_NAMESPACE+LIBRARY_NAME)
        error_message = paml.Primitive('error_message')
        error_message.description = 'Determine if calibration worked.'
        error_message.add_input('message', 'http://www.w3.org/2001/XMLSchema#string')
        protocol.document.add(error_message)
        sbol3.set_namespace(old_ns)

    return protocol.execute_primitive('error_message', message=message)

def pH_calibration_protocol() -> Tuple[paml.Protocol, Document]:
    #############################################
    # set up the document
    doc: Document = prepare_document()

    #############################################
    # Import the primitive libraries
    import_paml_libraries()

    #############################################
    # Create the protocol
    protocol: paml.Protocol = create_protocol()
    doc.add(protocol)

    # paml.import_library(LIBRARY_NAME)

    reaction_volume = protocol.input_value('reaction_volume', sbol3.OM_MEASURE, optional=True,
                                            default_value=sbol3.Measure(10, tyto.OM.milliliter))


    # 1. Decide whether to calibrate pH meter, and connect to initial node
    pH_meter_calibrated = make_pH_meter_calibrated(protocol)

    # 2. If not pH_meter_calibrated, then Calibrate the pH meter if needed
    calibrate_pH_meter = make_calibrate_pH_meter(protocol)
    # Link 1 -> 2 (False)
    pH_meter_calibrated.add_decision_output(protocol, False, calibrate_pH_meter)

    # 3. If pH_meter_calibrated, then inventorize and confirm materials
    inventorise_and_confirm_materials = make_inventorise_and_confirm_materials(protocol, reaction_volume)
    # Link 1 -> 3 (True)
    pH_meter_calibrated.add_decision_output(protocol, True, inventorise_and_confirm_materials)

    # 4. Decide whether calibration was successful
    is_calibration_successful = make_is_calibration_successful(protocol, calibrate_pH_meter)

    # Error Message Activity
    calibration_error = make_error_message(protocol, "Calibration Failed!")
    # Link 4 -> Error (False)
    is_calibration_successful.add_decision_output(protocol, False, calibration_error)

    # 5. Dispense Phosporhic Acid
    dispense_phosphoric_acid = make_dispense_phosphoric_acid(protocol)



    # Link 4 -> ready_to_adjust (True)

    # create the materials to be provisioned
    # ddh2o = create_h2o()
    # doc.add(ddh2o)

    # ludox = create_ludox()
    # doc.add(ludox)

    # add an optional parameter for specifying the wavelength
    # wavelength_param = protocol.input_value('wavelength', sbol3.OM_MEASURE, optional=True,
    #                                         default_value=sbol3.Measure(600, tyto.OM.nanometer))

    # # actual steps of the protocol
    # # get a plate
    # plate = create_plate(protocol)

    # # put ludox and water in selected wells
    # provision_h2o(protocol, plate, ddh2o)
    # provision_ludox(protocol, plate, ludox)

    # # measure the absorbance
    # measure = measure_absorbance(protocol, plate, wavelength_param)

    # output = protocol.designate_output('absorbance', sbol3.OM_MEASURE,
    #                                    measure.output_pin('measurements'))
    # protocol.order(protocol.get_last_step(), output)
    return protocol, doc


if __name__ == '__main__':
    new_protocol: paml.Protocol
    new_protocol, doc = pH_calibration_protocol()
    print('Validating and writing protocol')
    v = doc.validate()
    assert len(v) == 0, "".join(f'\n {e}' for e in v)

    rdf_filename = os.path.join(os.path.dirname(__file__), 'pH_calibration_protocol.nt')
    doc.write(rdf_filename, sbol3.SORTED_NTRIPLES)
    print(f'Wrote file as {rdf_filename}')

    # render and view the dot
    dot = new_protocol.to_dot()
    dot.render(f'{new_protocol.name}.gv')
    dot.view()
