# Core packages
import filecmp
import logging
import os
import tempfile
import unittest

import sbol3
import tyto
import xarray as xr

from labop import ContainerSpec, Protocol, SampleMap, Strings, serialize_sample_format
from labop.execution.execution_engine import ExecutionEngine
from labop.strings import Strings
from labop.utils.helpers import file_diff
from labop.utils.plate_coordinates import (
    coordinate_rect_to_row_col_pairs,
    coordinate_to_row_col,
    get_sample_list,
)
from labop_convert import DefaultBehaviorSpecialization
from labop_convert.behavior_specialization import DefaultBehaviorSpecialization

xr.set_options(display_expand_data=False)

logger: logging.Logger = logging.getLogger("samplemap_protocol")


OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)

filename = "".join(__file__.split(".py")[0].split("/")[-1:])


logger: logging.Logger = logging.Logger(__file__)
logger.setLevel(logging.INFO)

# Need logical to physical mapping
# Need volumes, and source contents
# Mix needs order for transfers (could be sub-protocol, media, then low volume)
# Need to surface assumptions about operations.  (Big then small, other heuristics?, type of reagent?)
#  Opentrons will perform in column order unless specified.


class TestProtocolEndToEnd(unittest.TestCase):
    def test_create_protocol(self):
        protocol, doc = Protocol.initialize_protocol()

        # The aliquots will be the coordinates of the SampleArray and SampleMap objects

        aliquot_ids = get_sample_list("A1:A4")

        # Make Components for the contents of the SampleArray
        reagent1 = sbol3.Component(
            "ddH2Oa", "https://identifiers.org/pubchem.substance:24901740"
        )
        reagent2 = sbol3.Component(
            "ddH2Ob", "https://identifiers.org/pubchem.substance:24901740"
        )
        reagents = [reagent1, reagent2]

        # TODO ContainerSpec without parameters will refer to a logical container of unspecified size and geometry
        source_spec = ContainerSpec(
            "abstractPlateRequirement1", name="abstractPlateRequirement1"
        )
        target_spec = ContainerSpec(
            "abstractPlateRequirement2", name="abstractPlateRequirement2"
        )

        # Arbitrary volume to use in specifying the reagents in the container.
        default_volume = sbol3.Measure(600, tyto.OM.microliter)

        reagent_arrays = {
            r: xr.DataArray(
                [default_volume.value] * len(aliquot_ids), dims=(Strings.SAMPLE)
            )
            for r in reagents
        }

        create_source = protocol.primitive_step(
            "EmptyContainer",
            specification=source_spec,
        )

        create_target = protocol.primitive_step(
            "EmptyContainer",
            specification=target_spec,
        )

        plan_mapping = serialize_sample_format(
            xr.DataArray(
                [
                    [
                        [[10.0 for target_aliquot in aliquot_ids]]
                        for source_aliquot in aliquot_ids
                    ]
                ],
                dims=(
                    f"source_{Strings.CONTAINER}",
                    f"source_{Strings.LOCATION}",
                    f"target_{Strings.CONTAINER}",
                    f"target_{Strings.LOCATION}",
                ),
                coords={
                    f"source_{Strings.CONTAINER}": [source_spec.name],
                    f"source_{Strings.LOCATION}": aliquot_ids,
                    f"target_{Strings.CONTAINER}": [target_spec.name],
                    f"target_{Strings.LOCATION}": aliquot_ids,
                },
            )
        )

        # The SampleMap specifies the sources and targets, along with the mappings.
        plan = SampleMap(
            sources=[create_source.output_pin("samples")],
            targets=[create_target.output_pin("samples")],
            values=plan_mapping,
        )

        # The outputs of the create_source and create_target calls will be identical
        # to the source_array and target_array.  They will not be on the output pin
        # until execution, but the SampleMap needs to reference them.
        transfer_by_map = protocol.primitive_step(
            "TransferByMap",
            source=create_source.output_pin("samples"),
            destination=create_target.output_pin("samples"),
            plan=plan,
            amount=sbol3.Measure(0, tyto.OM.milliliter),
            temperature=sbol3.Measure(30, tyto.OM.degree_Celsius),
        )

        measure = protocol.primitive_step(
            "MeasureAbsorbance",
            samples=create_target.output_pin("samples"),
            wavelength=sbol3.Measure(600, tyto.OM.nanometer),
        )

        result = protocol.designate_output(
            "absorbance", sbol3.OM_MEASURE, measure.output_pin("measurements")
        )

        protocol.order(result, protocol.final())

        ########################################
        # Validate and write the document

        agent = sbol3.Agent("test_agent")

        # Execute the protocol
        # In order to get repeatable timings, we use ordinal time in the test
        # where each timepoint is one second after the previous time point
        ee = ExecutionEngine(
            use_ordinal_time=True,
            failsafe=False,
            out_dir=OUT_DIR,
            specializations=[
                DefaultBehaviorSpecialization(),
                # MarkdownSpecialization("samplemap.md")
            ],
        )

        execution = ee.execute(
            protocol, agent, id="test_execution", parameter_values=[]
        )

        # result = xr.DataArray.from_dict(json.loads(execution.parameter_values[0].value.value.lookup().contents))

        execution.to_dot().render(os.path.join(OUT_DIR, filename))
        print("Validating and writing protocol")
        v = doc.validate()
        assert len(v) == 0, "".join(f"\n {e}" for e in v)

        temp_name = os.path.join(tempfile.gettempdir(), f"{filename}.nt")
        with open(temp_name, "w") as f:
            f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())
        print(f"Wrote file as {temp_name}")

        comparison_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "testfiles",
            filename + ".nt",
        )
        # with open(comparison_file, "w") as f:
        #     f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())
        print(f"Comparing against {comparison_file}")
        diff = "".join(file_diff(comparison_file, temp_name))
        print(f"Difference:\n{diff}")

        assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        print("File identical with test file")

    def test_xarray_graph(self):
        # Setup Nodes
        current_samples = ["s1", "s2"]
        next_samples = ["s3", "s4"]
        current_vol = xr.DataArray(
            [1.0, 3.0], dims=("volume"), coords={"volume": current_samples}
        )
        next_vol = xr.DataArray(
            [2.0, 4.0], dims=("volume"), coords={"volume": next_samples}
        )
        all_vol = xr.concat([current_vol, next_vol], dim="volume")

        # Setup Edges
        edges = xr.DataArray(
            [["s1", "s3"], ["s2", "s4"]],
            dims=("edge", "node"),
            coords={"node": ["source", "target"]},
        )

        # Make the graph
        ds = xr.Dataset({"nodes": all_vol, "edges": edges})

        # Extend the graph
        new_nodes = xr.DataArray(
            [4.0, 6.0], dims=("volume"), coords={"volume": ["s6", "s7"]}
        )
        new_edges = xr.DataArray(
            [["s3", "s6"], ["s4", "s7"]],
            dims=("edge", "node"),
            coords={"node": ["source", "target"]},
        )

        nodes = xr.concat([ds.nodes, new_nodes], dim="volume")
        edges = xr.concat([ds.edges, new_edges], dim="edge")

        ds1 = xr.Dataset({"nodes": nodes, "edges": edges})

        # Query the graph
        t = ds1.edges.sel(node="target")
        s = ds1.edges.sel(node="source")

        # Get targets where the target is not in the sources
        leaves = t.where(t.where(t.isin(s)).isnull(), drop=True)
        pass

    def test_mask(self):
        self.assertNotEqual(
            get_sample_list("A1:H12"),
            [
                "A1",
                "B1",
                "C1",
                "D1",
                "E1",
                "F1",
                "G1",
                "H1",
                "I1",
                "J1",
                "K1",
                "L1",
                "A2",
                "B2",
                "C2",
                "D2",
                "E2",
                "F2",
                "G2",
                "H2",
                "I2",
                "J2",
                "K2",
                "L2",
                "A3",
                "B3",
                "C3",
                "D3",
                "E3",
                "F3",
                "G3",
                "H3",
                "I3",
                "J3",
                "K3",
                "L3",
                "A4",
                "B4",
                "C4",
                "D4",
                "E4",
                "F4",
                "G4",
                "H4",
                "I4",
                "J4",
                "K4",
                "L4",
                "A5",
                "B5",
                "C5",
                "D5",
                "E5",
                "F5",
                "G5",
                "H5",
                "I5",
                "J5",
                "K5",
                "L5",
                "A6",
                "B6",
                "C6",
                "D6",
                "E6",
                "F6",
                "G6",
                "H6",
                "I6",
                "J6",
                "K6",
                "L6",
                "A7",
                "B7",
                "C7",
                "D7",
                "E7",
                "F7",
                "G7",
                "H7",
                "I7",
                "J7",
                "K7",
                "L7",
                "A8",
                "B8",
                "C8",
                "D8",
                "E8",
                "F8",
                "G8",
                "H8",
                "I8",
                "J8",
                "K8",
                "L8",
            ],
        )
        self.assertEqual(
            get_sample_list("A1:H12"),
            [
                "A1",
                "B1",
                "C1",
                "D1",
                "E1",
                "F1",
                "G1",
                "H1",
                "A2",
                "B2",
                "C2",
                "D2",
                "E2",
                "F2",
                "G2",
                "H2",
                "A3",
                "B3",
                "C3",
                "D3",
                "E3",
                "F3",
                "G3",
                "H3",
                "A4",
                "B4",
                "C4",
                "D4",
                "E4",
                "F4",
                "G4",
                "H4",
                "A5",
                "B5",
                "C5",
                "D5",
                "E5",
                "F5",
                "G5",
                "H5",
                "A6",
                "B6",
                "C6",
                "D6",
                "E6",
                "F6",
                "G6",
                "H6",
                "A7",
                "B7",
                "C7",
                "D7",
                "E7",
                "F7",
                "G7",
                "H7",
                "A8",
                "B8",
                "C8",
                "D8",
                "E8",
                "F8",
                "G8",
                "H8",
                "A9",
                "B9",
                "C9",
                "D9",
                "E9",
                "F9",
                "G9",
                "H9",
                "A10",
                "B10",
                "C10",
                "D10",
                "E10",
                "F10",
                "G10",
                "H10",
                "A11",
                "B11",
                "C11",
                "D11",
                "E11",
                "F11",
                "G11",
                "H11",
                "A12",
                "B12",
                "C12",
                "D12",
                "E12",
                "F12",
                "G12",
                "H12",
            ],
        )
        self.assertEqual(coordinate_rect_to_row_col_pairs("H11:H12")[1], (7, 11))
        self.assertEqual(coordinate_to_row_col("H12"), (7, 11))


if __name__ == "__main__":
    unittest.main()
