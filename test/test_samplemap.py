import datetime
import filecmp
import logging
import os
import tempfile
from typing import Tuple
import unittest
import xarray as xr
import json

import sbol3
import paml
from paml.execution_engine import ExecutionEngine
import uml
import tyto
from sbol3 import Document

logger: logging.Logger = logging.Logger("samplemap_protocol")

def prepare_document() -> Document:
    logger.info('Setting up document')
    doc = sbol3.Document()
    sbol3.set_namespace('https://bbn.com/scratch/')
    return doc

def create_protocol() -> paml.Protocol:
    logger.info('Creating protocol')
    protocol: paml.Protocol = paml.Protocol('samplemap_demo_protocol')
    protocol.name = "Protocol with a SampleMap Primitive"
    protocol.description = protocol.name
    return protocol

def initialize_protocol() -> Tuple[paml.Protocol, Document]:
    #############################################
    # set up the document
    doc: Document = prepare_document()

    #############################################
    # Import the primitive libraries
    paml.import_library('liquid_handling')
    paml.import_library('sample_arrays')

    #############################################
    # Create the protocol
    protocol: paml.Protocol = create_protocol()
    doc.add(protocol)
    return protocol, doc

class TestProtocolEndToEnd(unittest.TestCase):
    def test_create_protocol(self):
        protocol: paml.Protocol
        doc: sbol3.Document
        logger = logging.getLogger("LUDOX_protocol")
        logger.setLevel(logging.INFO)
        protocol, doc = initialize_protocol()

        # specification is an sbol.Identified, and we need to know the container
        # size to construct the sample map.
        source = protocol.primitive_step('EmptyContainer', specification=None)

        # parameter is the output (EmptyContainer returns a SampleArray Parameter)
        # source_samples will be type paml.SampleArray

        source_samples = source.compute_output(None, source.pin_parameter('samples'))
        destination = protocol.primitive_step('EmptyContainer', specification=None)
        plan = paml.SampleData(from_samples=source.samples)
        sample_map = protocol.primitive_step('TransferByMap', source=source, destination=destination, plan=plan)



        sample_map = plan.to_dataset()  # returns an xr.Dataset

        # sample_map will have only one variable which is named plan.identity
        # the initial sample_map_arr will be a 1D array of nan with length equal to the number of aliquots in source
        sample_map_arr = sample_map.to_array()  # get the xr.DataArray

        # We need to extend the 1D array to a 2D array (matrix) that defines the transfer
        sample_map_arr = sample_map_arr.rename({"aliquot", "source"})
        sample_map_arr = sample_map_arr.expand_dims("destination")
        sample_map_arr = sample_map_arr.assign_coords(coords = {"source" : sample_map_arr.coords, "destination" : sample_map_arr.coords})
        sample_map_arr.loc["A1", "A1"] = 1

        for k, v in dataset.data_vars.items():
            for dimension in v.dims:
                new_data = [8]*len(dataset[k].data)
                dataset.update({k : (dimension, new_data)})

        plan.values=json.dumps(sample_map.to_dict())



        ########################################
        # Validate and write the document

        agent = sbol3.Agent("test_agent")


        # Execute the protocol
        # In order to get repeatable timings, we use ordinal time in the test
        # where each timepoint is one second after the previous time point
        ee = ExecutionEngine(use_ordinal_time=True)
        parameter_values = [
            paml.ParameterValue(parameter=protocol.get_input("wavelength"),
                                value=uml.LiteralIdentified(value=sbol3.Measure(100, tyto.OM.nanometer)))
        ]
        execution = ee.execute(protocol, agent, id="test_execution", parameter_values=parameter_values)

        # Get the SampleData objects and attach values
        # get_data() returns a dict of output parameter ids to SampleData objects
        dataset = execution.get_data()

        for k, v in dataset.data_vars.items():
            for dimension in v.dims:
                new_data = [8]*len(dataset[k].data)
                dataset.update({k : (dimension, new_data)})

        execution.set_data(dataset)


        print('Validating and writing protocol')
        v = doc.validate()
        assert len(v) == 0, "".join(f'\n {e}' for e in v)

        temp_name = os.path.join(tempfile.gettempdir(), 'igem_ludox_data_test.nt')
        doc.write(temp_name, sbol3.SORTED_NTRIPLES)
        print(f'Wrote file as {temp_name}')

        comparison_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testfiles', 'igem_ludox_data_test.nt')
        # doc.write(comparison_file, sbol3.SORTED_NTRIPLES)
        print(f'Comparing against {comparison_file}')
        assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        print('File identical with test file')


if __name__ == '__main__':
    unittest.main()
