import sbol3
import logging
import labop

from typing import Tuple

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

def prepare_document(namespace='https://bioprotocols.org/demo/') -> sbol3.Document:
    logger.info('Setting up document')
    doc = sbol3.Document()
    sbol3.set_namespace(namespace)
    return doc

def create_protocol(display_id="demo_protocol", name="DemonstrationProtocol") -> labop.Protocol:
    logger.info('Creating protocol')
    protocol: labop.Protocol = labop.Protocol(display_id)
    protocol.name = name
    protocol.description = protocol.name
    return protocol

def initialize_protocol(display_id="demo_protocool", name="DemonstrationProtocol", namespace='https://bioprotocols.org/demo/') -> Tuple[labop.Protocol, sbol3.Document]:
    #############################################
    # set up the document
    doc: sbol3.Document = prepare_document(namespace=namespace)

    #############################################
    # Import the primitive libraries
    labop.import_library('liquid_handling')
    labop.import_library('sample_arrays')
    labop.import_library('spectrophotometry')

    #############################################
    # Create the protocol
    protocol: labop.Protocol = create_protocol(display_id=display_id, name=name)
    doc.add(protocol)
    return protocol, doc
