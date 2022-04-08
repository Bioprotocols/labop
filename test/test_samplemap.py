import datetime
import filecmp
import logging
import os
import tempfile
from typing import Tuple
import unittest
import numpy as np
import xarray as xr
import json

import sbol3
import paml
from paml.execution_engine import ExecutionEngine
from paml_convert.plate_coordinates import get_aliquot_list
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


# Need logical to physical mapping
# Need volumes, and source contents
# Mix needs order for transfers (could be sub-protocol, media, then low volume)
# Need to surface assumptions about operations.  (Big then small, other heuristics?, type of reagent?)
#  Opentrons will perform in column order unless specified.


class TestProtocolEndToEnd(unittest.TestCase):
    def test_create_protocol(self):
        protocol: paml.Protocol
        doc: sbol3.Document
        logger = logging.getLogger("transfer_map_protocol")
        logger.setLevel(logging.INFO)
        protocol, doc = initialize_protocol()

        # The aliquots will be the coordinates of the SampleArray and SampleMap objects
        num_aliquots = 4
        aliquot_ids = list(range(num_aliquots))

        # Make Components for the contents of the SampleArray
        reagent1 = sbol3.Component('ddH2Oa', 'https://identifiers.org/pubchem.substance:24901740')
        reagent2 = sbol3.Component('ddH2Ob', 'https://identifiers.org/pubchem.substance:24901740')
        reagents = [reagent1, reagent2]

        # TODO ContainerSpec without parameters will refer to a logical container of unspecified size and geometry
        source_spec = paml.ContainerSpec(name='abstractPlateRequirement1')
        target_spec = paml.ContainerSpec(name='abstractPlateRequirement2')

        # Arbitrary volume to use in specifying the reagents in the container.
        default_volume = sbol3.Measure(600, tyto.OM.microliter)


        # Creating the source SampleArray involves the following steps:
        # 1. Calling the EmptyContainer primitive with a defined specifcation
        # 2. Creating the SampleArray and referencing the specification.
        #    (SBOLFactory needs the specification to have an identity, which only
        #     happens in step 1.)
        # 3. Remove the EmptyContainer InputPin for "sample_array"
        # 4. Create a ValuePin for "sample_array" and add it to the input of the EmptyContainer call.
        #    (This is a place where we can map a SampleArray to a container)

        # 1.
        create_source = protocol.primitive_step('EmptyContainer', specification=source_spec)

        # 2.
        # The SampleArray is a 2D |aliquot| x |reagent| array, where values are volumes.
        # The aliquot dimension uses aliquot_ids (specified above) as coordinates.
        # The reagent dimension uses reagents (specified above) as coordinates.
        #
        # Results in the DataArray representing contents:
        #
        # <xarray.DataArray (aliquot: 4, contents: 2)>
        # array([[600., 600.],
        #        [600., 600.],
        #        [600., 600.],
        #        [600., 600.]])
        # Coordinates:
        #   * aliquot   (aliquot) int64 0 1 2 3
        #   * contents  (contents) <U30 'https://bbn.com/scratch/ddH2Oa' 'https://bbn.c...
        source_array = paml.SampleArray(
            name="source",
            container_type=source_spec,
            contents=json.dumps(xr.DataArray([[default_volume.value
                                                for reagent in reagents]
                                                for id in aliquot_ids],
                                             dims=("aliquot", "contents"),
                                             coords={"aliquot": aliquot_ids,
                                                     "contents": [r.identity for r in reagents]}).to_dict()))
        # 3.
        sample_array_parameter = create_source.pin_parameter("sample_array")
        [old_input] = [x for x in create_source.inputs if x.name == "sample_array"]
        create_source.inputs.remove(old_input)

        # 4.
        create_source.inputs.append(uml.ValuePin(name="sample_array", is_ordered=sample_array_parameter.property_value.is_ordered,
                                          is_unique=sample_array_parameter.property_value.is_unique, value=uml.literal(source_array)))


        # Similar to the source_array, above, we specify an analogous target_array
        # 1.
        create_target = protocol.primitive_step('EmptyContainer', specification=target_spec)

        # 2.
        target_array = paml.SampleArray(
            name="target",
            container_type=target_spec,
            contents=json.dumps(xr.DataArray([[0.0
                                                for reagent in reagents]
                                                for id in aliquot_ids],
                                             dims=("aliquot", "contents"),
                                             coords={"aliquot": aliquot_ids,
                                                     "contents": [r.identity for r in reagents]}).to_dict()))

        # 3.
        sample_array_parameter = create_target.pin_parameter("sample_array")
        [old_input] = [x for x in create_target.inputs if x.name == "sample_array"]
        create_target.inputs.remove(old_input)

        # 4.
        create_target.inputs.append(uml.ValuePin(name="sample_array", is_ordered=sample_array_parameter.property_value.is_ordered,
                                          is_unique=sample_array_parameter.property_value.is_unique, value=uml.literal(target_array)))


        # plan_mapping is a 4D array of volumes for transfers:
        #    (source_array, source_aliquot) --volume--> (target_array, target_aliquot)
        #
        # The plan_mapping from above is a single source_array and single target_array:
        #
        # <xarray.DataArray (source_array: 1, source_aliquot: 4, target_array: 1,
        #                    target_aliquot: 4)>
        # array([[[[10., 10., 10., 10.]],

        #         [[10., 10., 10., 10.]],

        #         [[10., 10., 10., 10.]],

        #         [[10., 10., 10., 10.]]]])
        # Coordinates:
        #   * source_array    (source_array) <U6 'source'
        #   * source_aliquot  (source_aliquot) int64 0 1 2 3
        #   * target_array    (target_array) <U6 'target'
        #   * target_aliquot  (target_aliquot) int64 0 1 2 3

        plan_mapping = json.dumps(xr.DataArray([[[[10.0
                                                for target_aliquot in aliquot_ids]
                                                for target_array in [target_array.name]]
                                                for source_aliquot in aliquot_ids]
                                                for source_array in [source_array.name]],
                                           dims=("source_array", "source_aliquot", "target_array", "target_aliquot",),
                                           coords={"source_array": [source_array.name],
                                                   "source_aliquot": aliquot_ids,
                                                   "target_array": [target_array.name],
                                                   "target_aliquot": aliquot_ids
                                                   }).to_dict())



        # The SampleMap specifies the sources and targets, along with the mappings.
        plan = paml.SampleMap(
                            sources=[source_array],
                            targets=[target_array],
                            values=plan_mapping)

        # The outputs of the create_source and create_target calls will be identical
        # to the source_array and target_array.  They will not be on the output pin
        # until execution, but the SampleMap needs to reference them.
        transfer_by_map = protocol.primitive_step(
                            'TransferByMap',
                            source=create_source.output_pin('samples'),
                            destination=create_target.output_pin('samples'),
                            plan=plan)




        ########################################
        # Validate and write the document

        agent = sbol3.Agent("test_agent")


        # Execute the protocol
        # In order to get repeatable timings, we use ordinal time in the test
        # where each timepoint is one second after the previous time point
        ee = ExecutionEngine(use_ordinal_time=True)
        parameter_values = [
            # paml.ParameterValue(parameter=protocol.get_input("wavelength"),
            #                     value=uml.LiteralIdentified(value=sbol3.Measure(100, tyto.OM.nanometer)))
        ]
        execution = ee.execute(protocol, agent, id="test_execution", parameter_values=parameter_values)

        print('Validating and writing protocol')
        v = doc.validate()
        assert len(v) == 0, "".join(f'\n {e}' for e in v)

        temp_name = os.path.join(tempfile.gettempdir(), 'igem_ludox_data_test.nt')
        doc.write(temp_name, sbol3.SORTED_NTRIPLES)
        print(f'Wrote file as {temp_name}')

        comparison_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'testfiles', 'sample_map_test.nt')
        doc.write(comparison_file, sbol3.SORTED_NTRIPLES)
        print(f'Comparing against {comparison_file}')
        assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        print('File identical with test file')


if __name__ == '__main__':
    unittest.main()
