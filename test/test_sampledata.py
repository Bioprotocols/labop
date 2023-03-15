import filecmp
import logging
import os
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader

import sbol3
import tyto
import xarray as xr
from numpy import nan
from tyto import OM

import labop
import uml
from labop import Protocol
from labop.execution_engine import ExecutionEngine
from labop.utils.helpers import file_diff
from labop.utils.plate_coordinates import get_sample_list

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)


# Save testfiles as artifacts when running in CI environment,
# else save them to a local temp directory
if "GH_TMPDIR" in os.environ:
    TMPDIR = os.environ["GH_TMPDIR"]
else:
    TMPDIR = tempfile.gettempdir()

protocol_def_file = os.path.join(
    os.path.dirname(__file__), "../examples/LUDOX_protocol.py"
)


def load_ludox_protocol(protocol_filename):
    loader = SourceFileLoader("ludox_protocol", protocol_filename)
    spec = spec_from_loader(loader.name, loader)
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


protocol_def = load_ludox_protocol(protocol_def_file)


class TestProtocolEndToEnd(unittest.TestCase):
    def test_dataset_to_dataframe(self):
        protocol, doc = Protocol.initialize_protocol()
        protocol.name = "sample_data_demo_protocol"

        reagents = [
            "fluorescene",
            "sulforhodamine101",
            "cascadeBlue",
            "nanocym",
            "water",
            "pbs",
        ]
        samples = get_sample_list(geometry="A1:H12")

        def volume_in_sample(reagent, sample):
            if "A" in sample:
                if reagent == "fluorescene" or reagent == "water":
                    return 1.0
            elif "B" in sample:
                if reagent == "cascadeBlue" or reagent == "pbs":
                    return 1.0
            return nan

        # sample_data = xr.DataArray(
        #     [10.0 for sample in samples],
        #     dims=("sample"),
        #     coords={"sample": samples}
        #     )
        # initial_contents = xr.DataArray(samples,
        #                                 dims=(labop.Strings.SAMPLE),
        #                                 coords={labop.Strings.SAMPLE: samples})
        # sample_array = labop.SampleArray(container_type=labop.ContainerSpec("dummy_spec"),
        #                                  initial_contents=labop.serialize_sample_format(initial_contents))

        # container_spec = labop.ContainerSpec('abstractPlateRequirement1',
        #                                  name='abstractPlateRequirement1')
        # create_source = protocol.primitive_step('EmptyContainer', specification=container_spec, sample_array=sample_array)

        # Define the type of container
        container_type = container_type = labop.ContainerSpec("deep96")

        # Create an activity to create the container.
        create_source = protocol.primitive_step(
            "EmptyContainer", specification=container_type
        )

        metadata_filename = "test/metadata/measure_absorbance.xlsx"

        load_excel = protocol.primitive_step(
            "ExcelMetadata",
            for_samples=create_source.output_pin("samples"),
            filename=metadata_filename,
        )

        create_coordinates = protocol.primitive_step(
            "PlateCoordinates",
            source=create_source.output_pin("samples"),
            coordinates="A1:B12",
        )

        measure_absorbance = protocol.primitive_step(
            "MeasureAbsorbance",
            samples=create_coordinates.output_pin("samples"),
            wavelength=sbol3.Measure(600, OM.nanometer),
        )

        meta1 = protocol.primitive_step(
            "JoinMetadata",
            dataset=measure_absorbance.output_pin("measurements"),
            metadata=load_excel.output_pin("metadata"),
        )

        outnode = protocol.designate_output(
            "dataset",
            "http://bioprotocols.org/labop#Dataset",
            source=meta1.output_pin("enhanced_dataset"),
        )

        protocol.order(outnode, protocol.final())

        filename = protocol.name
        protocol.to_dot().render(os.path.join(OUT_DIR, filename))

        ee = ExecutionEngine(
            failsafe=False,
            sample_format="xarray",
            use_ordinal_time=True,
            dataset_file=f"{filename}_data",  # name of xlsx file (w/o suffix)
            out_dir=OUT_DIR,
        )
        execution = ee.execute(
            protocol,
            sbol3.Agent("test_agent"),
            id="test_execution",
            parameter_values=[],
        )

        execution.to_dot().render(os.path.join(OUT_DIR, f"{protocol.name}_execution"))

        # dataset = execution.parameter_values[0].value.get_value()
        # xr_dataset = labop.sort_samples(dataset.to_dataset())
        # df = xr_dataset.to_dataframe()
        # df.to_excel(os.path.join(OUT_DIR, "dataset.xlsx"))

        print("Validating and writing protocol")
        v = doc.validate()
        assert len(v) == 0, "".join(f"\n {e}" for e in v)

        nt_file = f"{filename}.nt"
        temp_name = os.path.join(TMPDIR, nt_file)

        # At some point, rdflib began inserting an extra newline into
        # N-triple serializations, which breaks file comparison.
        # Here we strip extraneous newlines, to maintain reverse compatibility
        with open(temp_name, "w") as f:
            f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())
        print(f"Wrote file as {temp_name}")

        comparison_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "testfiles",
            nt_file,
        )
        # with open(comparison_file, "w") as f:
        #     f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())
        print(f"Comparing against {comparison_file}")
        diff = "".join(file_diff(comparison_file, temp_name))
        print(f"Difference:\n{diff}")
        assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        print("File identical with test file")

    @unittest.skip(reason="tmp remove for dev")
    def test_create_protocol(self):
        protocol: labop.Protocol
        doc: sbol3.Document
        logger = logging.getLogger("LUDOX_protocol")
        logger.setLevel(logging.INFO)
        protocol, doc = protocol_def.ludox_protocol()

        ########################################
        # Validate and write the document

        agent = sbol3.Agent("test_agent")

        # Execute the protocol
        # In order to get repeatable timings, we use ordinal time in the test
        # where each timepoint is one second after the previous time point
        ee = ExecutionEngine(out_dir=OUT_DIR, use_ordinal_time=True)
        parameter_values = [
            labop.ParameterValue(
                parameter=protocol.get_input("wavelength"),
                value=uml.LiteralIdentified(
                    value=sbol3.Measure(100, tyto.OM.nanometer)
                ),
            )
        ]
        execution = ee.execute(
            protocol,
            agent,
            id="test_execution",
            parameter_values=parameter_values,
        )

        # Get the SampleData objects and attach values
        # get_data() returns a dict of output parameter ids to SampleData objects
        dataset = execution.get_data()

        for id, ds in dataset.items():
            for k, v in ds.data_vars.items():
                for dimension in v.dims:
                    new_data = [8] * len(ds[k].data)
                    ds.update({k: (dimension, new_data)})

        execution.set_data(dataset)

        print("Validating and writing protocol")
        v = doc.validate()
        assert len(v) == 0, "".join(f"\n {e}" for e in v)

        temp_name = os.path.join(TMPDIR, "igem_ludox_data_test.nt")

        # At some point, rdflib began inserting an extra newline into
        # N-triple serializations, which breaks file comparison.
        # Here we strip extraneous newlines, to maintain reverse compatibility
        with open(temp_name, "w") as f:
            f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())
        print(f"Wrote file as {temp_name}")

        comparison_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "testfiles",
            "igem_ludox_data_test.nt",
        )

        diff = "".join(file_diff(comparison_file, temp_name))
        print(f"Difference: {diff}")
        # with open(comparison_file, 'w') as f:
        #     f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())
        print(f"Comparing against {comparison_file}")
        assert filecmp.cmp(temp_name, comparison_file), "Files are not identical"
        print("File identical with test file")


if __name__ == "__main__":
    unittest.main()
