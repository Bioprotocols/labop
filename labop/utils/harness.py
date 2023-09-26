import logging
import os
from abc import ABC
from datetime import datetime
from typing import Callable, List

import sbol3
from isort import file

from labop.execution_engine import ExecutionEngine
from labop.library import import_library
from labop.parameter_value import ParameterValue
from labop.protocol import Protocol
from labop.utils.helpers import prepare_document
from labop_convert import BehaviorSpecialization
from labop_convert.behavior_specialization import BehaviorSpecialization

l = logging.Logger(__file__)
l.setLevel(logging.INFO)
ConsoleOutputHandler = logging.StreamHandler()
l.addHandler(ConsoleOutputHandler)


class ProtocolArtifact(ABC):
    summary: str = ""

    def summary(self):
        return ""

    def results_summary(self):
        return self._summary


class ProtocolDiagram(ProtocolArtifact):
    pass


class ProtocolNTuples(ProtocolArtifact):
    pass


class ProtocolExecutionNTuples(ProtocolArtifact):
    pass


class ProtocolExecutionDiagram(ProtocolArtifact):
    pass


class ProtocolSampleTrace(ProtocolArtifact):
    pass


class ProtocolSpecialization(ProtocolArtifact):
    specialization: BehaviorSpecialization

    def __init__(self, specialization: BehaviorSpecialization) -> None:
        super().__init__()
        self.specialization = specialization

    def write_output(self, filename_prefix: str):
        pass


class ProtocolHarness:
    entry_point: Callable
    artifacts: List[ProtocolArtifact] = []
    base_artifacts: List[ProtocolArtifact] = [
        ProtocolNTuples(),
        ProtocolDiagram(),
        ProtocolExecutionDiagram(),
        ProtocolSampleTrace(),
        ProtocolExecutionNTuples(),
    ]
    namespace: str
    protocol_name: str
    protocol_long_name: str
    protocol_version: str
    protocol_description: str
    output_dir: str = "artifacts"
    libraries: List[str] = [
        "liquid_handling",
        "plate_handling",
        "spectrophotometry",
        "sample_arrays",
    ]
    parameter_values: List[ParameterValue] = []
    execution_id: str = None
    agent: sbol3.Agent = sbol3.Agent("labop_harness")
    _doc: sbol3.Document = None
    _protocol: Protocol = None

    def __init__(self, *args, **kwargs):
        self.entry_point = kwargs["entry_point"]
        self.artifacts = (
            kwargs["artifacts"] if "artifacts" in kwargs else self.artifacts
        )
        self.artifacts = (
            kwargs["base_artifacts"]
            if "base_artifacts" in kwargs
            else self.base_artifacts
        )
        self.namespace = kwargs["namespace"]
        self.protocol_name = kwargs["protocol_name"]
        self.protocol_long_name = kwargs["protocol_long_name"]
        self.protocol_version = kwargs["protocol_version"]
        self.protocol_description = kwargs["protocol_description"]
        self.output_dir = (
            kwargs["output_dir"] if "output_dir" in kwargs else self.output_dir
        )
        self.libraries = (
            kwargs["libraries"] if "libraries" in kwargs else self.libraries
        )
        self.parameter_values = (
            kwargs["parameter_values"]
            if "parameter_values" in kwargs
            else self.parameter_values
        )
        self.execution_id = (
            kwargs["execution_id"] if "execution_id" in kwargs else self.execution_id
        )
        self.agent = kwargs["agent"] if "agent" in kwargs else self.agent
        self._doc = None
        self._protocol = None

    def import_libraries(self):
        for library in self.libraries:
            import_library(library)

    def generate_protocol(self) -> Protocol:
        self.import_libraries()
        self._protocol = Protocol(self.protocol_name)
        self._protocol.name = self.protocol_long_name
        self._protocol.version = self.protocol_version
        self._protocol.description = self.protocol_description
        self._doc.add(self._protocol)
        self._protocol = self.entry_point(self._doc, self._protocol)
        l.info("Validating and writing protocol")
        v = self._doc.validate()
        assert len(v) == 0, "".join(f"\n {e}" for e in v)

        return self._protocol

    def prepare_document(self) -> sbol3.Document:
        self._doc = prepare_document(namespace=self.namespace)
        return self._doc

    def filename_prefix(self) -> str:
        return self.entry_point.__name__

    def ntuples_filename(self) -> str:
        return self.filename_prefix() + ".nt"

    def diagram_filename(self) -> str:
        return self.filename_prefix() + ".diagram"

    def dataset_filename(self) -> str:
        return self.filename_prefix() + ".data.xslx"

    def read_protocol(self, filename: str = None):
        filename = self.ntuples_filename() if filename is None else filename
        self.prepare_document()
        self._doc.read(filename, "nt")
        self._protocol = doc.find(f"{self.namespace}{self.protocol_name}")

        return self._protocol, self._doc

    def execution_engine(
        self,
        specializations: List[BehaviorSpecialization],
        dataset_filename: str,
    ) -> ExecutionEngine:
        return ExecutionEngine(
            out_dir=self.output_dir,
            specializations=specializations,
            failsafe=False,
            sample_format="xarray",
            dataset_file=dataset_filename,
        )

    def get_execution_id(self) -> str:
        if self.execution_id is None:
            self.execution_id = (
                (f"harness_execution_{self.protocol_name}_{datetime.now()}")
                .replace(" ", "_")
                .replace("-", "_")
                .replace(":", "_")
                .replace(".", "_")
            )
        return self.execution_id

    def artifacts_summary(self) -> str:
        summary = ""
        for a in self.artifacts:
            summary += f"    - {a.__class__.__name__}: {a.summary()}\n"
        return summary

    def artifacts_results_summary(self) -> str:
        summary = ""
        for a in self.artifacts:
            summary += f"    - {a.__class__.__name__}: {a.results_summary()}\n"
        return summary

    def run(self, base_dir="."):
        l.info(
            f"""
{'*'*80}

    LabOP Protocol Harness

    Configuration:
    --------------
    Artifacts:
{self.artifacts_summary()}
{'*'*80}
        """
        )
        full_output_dir = os.path.join(base_dir, self.output_dir)
        # Store outputs in full_output_dir
        os.makedirs(full_output_dir, exist_ok=True)
        l.info("Writing protocol artifacts to: {full_output_dir}")

        all_artifacts = self.base_artifacts + self.artifacts

        generate_nt_file = any(
            a for a in all_artifacts if isinstance(a, ProtocolNTuples)
        )
        nt_filename = os.path.join(full_output_dir, self.ntuples_filename())

        # 1) Get the self._protocol either by generating it or reading it
        if generate_nt_file:
            self.prepare_document()
            self.generate_protocol()
        else:
            l.info(f"Bypassing Protocol Generation, looking for existing .nt file ...")
            if os.path.exists(nt_filename):
                l.info(f"Found .nt file: {nt_filename}")
                self.read_protocol()

        # 2) Create any protocol-specific artifacts
        if generate_nt_file:
            with open(nt_filename, "w") as f:
                l.info(f"Saving protocol [{nt_filename}].")
                f.write(self._doc.write_string(sbol3.SORTED_NTRIPLES).strip())
        if any(a for a in all_artifacts if isinstance(a, ProtocolDiagram)):
            self._protocol.to_dot().render(
                os.path.join(full_output_dir, self.diagram_filename()),
                cleanup=True,
            )

        # 3) Generate execution-specific artifacts
        sample_trace = any(
            a for a in all_artifacts if isinstance(a, ProtocolSampleTrace)
        )
        dataset_filename = (
            os.path.join(full_output_dir, self.dataset_filename())
            if sample_trace
            else None
        )

        specializations = [
            a for a in all_artifacts if isinstance(a, ProtocolSpecialization)
        ]

        ee = self.execution_engine(
            [s.specialization for s in specializations], dataset_filename
        )

        execution = ee.execute(
            self._protocol,
            self.agent,
            id=self.get_execution_id(),
            parameter_values=self.parameter_values,
        )

        if any(a for a in all_artifacts if isinstance(a, ProtocolExecutionNTuples)):
            with open(nt_filename, "w") as f:
                f.write(self._doc.write_string(sbol3.SORTED_NTRIPLES).strip())

        for specialization in specializations:
            results = specialization.output()
            specialization_classname = specialization.__class__.__name__
            specialization_dir = os.path.join(full_output_dir, specialization_classname)
            os.makedirs(specialization_dir, exist_ok=True)
            for i, result in enumerate(results):
                # extension = mimetypes.guess_extension(magic.Magic(mime=True).from_file(result))
                extension = "json"
                result_file = os.path.join(
                    specialization_dir,
                    f"{specialization_classname}_result_{i}.{extension}",
                )
                with open(result_file, "w") as f:
                    f.write(result)

        l.info(
            f"""
{'*'*80}

    Harness Results Summary

    Artifacts:
{self.artifacts_results_summary()}
{'*'*80}
        """
        )
