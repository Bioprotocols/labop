import filecmp
import glob
import json
import logging
import os
import shutil
from abc import ABC
from datetime import datetime
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from typing import Any, Callable, Dict, List, Optional, Union

import sbol3

from labop import ProtocolExecution
from labop.execution import ExecutionEngine
from labop.library import import_library
from labop.parameter_value import ParameterValue
from labop.protocol import Protocol
from labop.utils.helpers import file_diff, prepare_document
from labop_convert import BehaviorSpecialization

l = logging.Logger(__file__)
l.setLevel(logging.INFO)
ConsoleOutputHandler = logging.StreamHandler()
l.addHandler(ConsoleOutputHandler)


class ProtocolArtifactStatus:
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"


class ProtocolArtifact(ABC):
    results: Dict[str, Any] = None
    status: str = None
    filename: str = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.status = ProtocolArtifactStatus.PENDING
        self.results = {}

    def results_summary(self) -> str:
        return f"{json.dumps(self.results, indent=4)}"

    def configuration_summary(self, verbose=False) -> str:
        return ""


class ProtocolNTuples(ProtocolArtifact):
    cached_protocol_file: Optional[str] = None
    namespace: str
    protocol_name: str
    protocol_long_name: str
    protocol_version: str
    protocol_description: str
    _protocol: Protocol = None
    _doc: sbol3.Document = None
    next: Optional[ProtocolArtifact] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached_protocol_file = (
            kwargs["cached_protocol_file"] if "cached_protocol_file" in kwargs else None
        )
        self.namespace = kwargs["namespace"] if "namespace" in kwargs else None
        self.protocol_name = (
            kwargs["protocol_name"] if "protocol_name" in kwargs else None
        )
        self.protocol_long_name = (
            kwargs["protocol_long_name"] if "protocol_long_name" in kwargs else None
        )
        self.protocol_version = (
            kwargs["protocol_version"] if "protocol_version" in kwargs else None
        )
        self.protocol_description = (
            kwargs["protocol_description"] if "protocol_description" in kwargs else None
        )
        self.next = kwargs["next"] if "next" in kwargs else None
        self._doc = self.prepare_document()
        self._protocol = None

    def read_protocol(self, filename: str = None):
        filename = self.cached_protocol_file if filename is None else filename
        self._doc.read(filename, "nt")
        self._protocol = self._doc.find(f"{self.namespace}{self.protocol_name}")
        return self._protocol, self._doc

    def import_libraries(self, libraries: List[str]):
        self.results["libraries"] = []
        for library in libraries:
            import_library(library)
            self.results["libraries"].append(library)

    def generate_protocol(self, harness: "ProtocolHarness") -> Protocol:
        self.import_libraries(harness.libraries)
        entry_point = harness.entry_point
        self._protocol = Protocol(harness.protocol_name)
        self._protocol.name = harness.protocol_long_name
        self._protocol.version = harness.protocol_version
        self._protocol.description = harness.protocol_description
        self.results["protocol"] = {
            "name": self.protocol_name,
            "version": self._protocol.version,
        }
        self._doc.add(self._protocol)
        self._protocol = entry_point(self._doc, self._protocol)
        l.info("Validating and writing protocol")
        v = self._doc.validate()

        if len(v) > 0:
            self.results["protocol"]["validation"] = "".join(f"\n {e}" for e in v)
            self.status = ProtocolArtifactStatus.FAIL
        else:
            self.results["protocol"]["validation"] = ProtocolArtifactStatus.PASS
            self.status = ProtocolArtifactStatus.PASS

        return self._protocol

    def prepare_document(self) -> sbol3.Document:
        self._doc = prepare_document(namespace=self.namespace)
        self.results["document"] = {"namespace": self.namespace}
        return self._doc

    def ntuples_filename(self, filename_prefix) -> str:
        return filename_prefix + ".nt"

    def generate_artifact(self, harness: "ProtocolHarness"):
        if self.cached_protocol_file is not None:
            l.info(f"Bypassing Protocol Generation, looking for existing .nt file ...")
            if os.path.exists(self.cached_protocol_file):
                l.info(f"Found .nt file: {self.cached_protocol_file}")
                self.read_protocol()

        self.filename = (
            os.path.join(
                harness.full_output_dir,
                self.ntuples_filename(harness.filename_prefix()),
            )
            if self.filename is None
            else self.filename
        )
        try:
            self.generate_protocol(harness)

            assert self._protocol is not None, f"Protocol was not generated ... "

            # with open(self.filename, "w") as f:
            l.info(f"Saving protocol [{self.filename}].")
            # f.write(self._doc.write_string(sbol3.SORTED_NTRIPLES).strip())
            self.results["nt_filename"] = self.filename
            # self._doc.write(self.filename, sbol3.SORTED_NTRIPLES)
            with open(self.filename, "w") as f:
                f.write(self._doc.write_string(sbol3.SORTED_NTRIPLES).strip())

        except Exception as e:
            self.status = ProtocolArtifactStatus.FAIL
            self.results["exception"] = str(e)


class ProtocolDownstreamArtifact(ProtocolArtifact):
    protocol_artifact: ProtocolNTuples = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol_artifact = (
            kwargs["protocol_artifact"] if "protocol_artifact" in kwargs else None
        )

    def protocol(self):
        return self.protocol_artifact._protocol

    def protocol_name(self):
        return self.protocol_artifact.protocol_name


class ProtocolDiagram(ProtocolDownstreamArtifact):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def diagram_filename(self, filename_prefix: str) -> str:
        return filename_prefix + ".diagram"

    def generate_artifact(self, harness: "ProtocolHarness"):
        self.filename = (
            os.path.join(
                harness.full_output_dir,
                self.diagram_filename(harness.filename_prefix()),
            )
            if self.filename is None
            else self.filename
        )
        try:
            self.protocol().to_dot().render(
                self.filename, cleanup=True, overwrite_source=True
            )
            self.results["filename"] = self.filename
            self.status = ProtocolArtifactStatus.PASS
        except Exception as e:
            self.results["exception"] = str(e)
            self.status = ProtocolArtifactStatus.FAIL


class ProtocolRubric(ProtocolDownstreamArtifact):
    filename: str = None

    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = filename

    def generate_artifact(self, harness: "ProtocolHarness"):
        # diff = ""
        try:
            diff = file_diff(self.filename, self.protocol_artifact.filename)
            # print(f"Difference: {diff}")
            assert filecmp.cmp(
                self.protocol_artifact.filename, self.filename
            ), "Files are not identical"
            self.results["filename"] = self.filename
            self.status = ProtocolArtifactStatus.PASS
        except Exception as e:
            self.results["exception"] = str(e)
            self.status = ProtocolArtifactStatus.FAIL
        self.results["diff"] = diff


class ProtocolExecutionNTuples(ProtocolDownstreamArtifact):
    agent: Union[sbol3.Agent, str] = None
    execution: ProtocolExecution = None
    execution_id: str = None
    parameter_values: List[ParameterValue] = None
    execution_engine: ExecutionEngine = None
    specializations: List[BehaviorSpecialization] = None
    dataset_filename: str = None
    execution_kwargs: Dict[str, Any] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = (
            kwargs["agent"] if "agent" in kwargs else sbol3.Agent("labop_harness")
        )
        if isinstance(self.agent, str):
            self.agent = sbol3.Agent(self.agent)

        self.execution_id = (
            kwargs["execution_id"] if "execution_id" in kwargs else self.execution_id
        )
        self.parameter_values = (
            kwargs["parameter_values"]
            if "parameter_values" in kwargs
            else self.parameter_values
        )

        self.dataset_filename = (
            kwargs["dataset_filename"]
            if "dataset_filename" in kwargs
            else "dataset.xslx"
        )
        self.specializations = (
            kwargs["specializations"]
            if "specializations" in kwargs
            else self.specializations
        )
        self.execution_kwargs = (
            kwargs["execution_kwargs"] if "execution_kwargs" in kwargs else {}
        )
        self.execution_engine = None

    def _execution_engine(self, output_dir) -> ExecutionEngine:
        specializations = [s.specialization for s in self.specializations]
        kwargs = {
            "out_dir": output_dir,
            "specializations": specializations,
            "failsafe": False,
            "sample_format": "xarray",
            "dataset_file": self.dataset_filename,
        }
        kwargs.update(self.execution_kwargs)

        return ExecutionEngine(**kwargs)

    def ntuples_filename(self, filename_prefix) -> str:
        return filename_prefix + ".nt"

    def get_execution_id(self) -> str:
        if self.execution_id is None:
            self.execution_id = (
                (f"harness_execution_{self.protocol_name()}_{datetime.now()}")
                .replace(" ", "_")
                .replace("-", "_")
                .replace(":", "_")
                .replace(".", "_")
            )
        return self.execution_id

    def generate_artifact(self, harness: "ProtocolHarness"):
        self.execution_engine = self._execution_engine(harness.full_output_dir)
        self.execution: ProtocolExecution = self.execution_engine.execute(
            self.protocol(),
            self.agent,
            id=self.get_execution_id(),
            parameter_values=self.parameter_values,
        )

        try:
            self.filename = (
                os.path.join(
                    harness.full_output_dir,
                    self.ntuples_filename(harness.filename_prefix()),
                )
                if self.filename is None
                else self.filename
            )
            with open(self.filename, "w") as f:
                f.write(
                    self.protocol().document.write_string(sbol3.SORTED_NTRIPLES).strip()
                )
            self.results["filename"] = self.filename
            self.status = ProtocolArtifactStatus.PASS

        except Exception as e:
            self.status = ProtocolArtifactStatus.FAIL
            self.results["exception"] = str(e)


class ProtocolExecutionDownstreamArtifact(ProtocolDownstreamArtifact):
    protocol_execution_artifact: ProtocolExecutionNTuples = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.protocol_execution_artifact = (
            kwargs["protocol_execution_artifact"]
            if "protocol_execution_artifact" in kwargs
            else None
        )


class ProtocolExecutionRubric(ProtocolExecutionDownstreamArtifact):
    filename: str = None
    overwrite_rubric: bool = False

    def __init__(self, filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = filename

        self.overwrite_rubric = (
            kwargs["overwrite_rubric"]
            if "overwrite_rubric" in kwargs
            else self.overwrite_rubric
        )

    def generate_artifact(self, harness: "ProtocolHarness"):
        diff = ""
        try:
            if self.overwrite_rubric:
                l.warn(
                    f"Overwriting rubric at: {self.filename} with {self.protocol_execution_artifact.filename}"
                )
                shutil.copyfile(
                    self.protocol_execution_artifact.filename, self.filename
                )

            diff = file_diff(self.filename, self.protocol_execution_artifact.filename)

            # print(f"Difference: {diff}")
            assert filecmp.cmp(
                self.protocol_execution_artifact.filename, self.filename
            ), "Files are not identical"
            self.results["filename"] = self.filename
            self.status = ProtocolArtifactStatus.PASS
        except Exception as e:
            self.results["exception"] = str(e)
            self.status = ProtocolArtifactStatus.FAIL
        self.results["diff"] = diff


class ProtocolExecutionDiagram(ProtocolExecutionDownstreamArtifact):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def diagram_filename(self, filename_prefix: str) -> str:
        return filename_prefix + ".execution.diagram"

    def generate_artifact(
        self,
        harness: "ProtocolHarness",
    ):
        self.filename = (
            os.path.join(
                harness.full_output_dir,
                self.diagram_filename(harness.filename_prefix()),
            )
            if self.filename is None
            else self.filename
        )
        try:
            self.protocol_execution_artifact.execution.to_dot().render(
                self.filename,
                cleanup=True,
                overwrite_source=True,
            )
            self.results["filename"] = self.filename
            self.status = ProtocolArtifactStatus.PASS
        except Exception as e:
            self.results["exception"] = str(e)
            self.status = ProtocolArtifactStatus.FAIL


class ProtocolSampleTrace(ProtocolExecutionDownstreamArtifact):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate_artifact(self, harness: "ProtocolHarness"):
        try:
            results = glob.glob(f"{harness.full_output_dir}/sample_graph*")
            sample_trace_dir = os.path.join(harness.full_output_dir, "sample_traces")
            os.makedirs(sample_trace_dir, exist_ok=True)
            for i, result in enumerate(results):
                # extension = mimetypes.guess_extension(magic.Magic(mime=True).from_file(result))
                shutil.move(result, sample_trace_dir)
            self.filename = sample_trace_dir
            self.status = ProtocolArtifactStatus.PASS
            self.results["filename"] = self.filename
        except Exception as e:
            self.status = ProtocolArtifactStatus.FAIL
            self.results["exception"] = str(e)
            l.exception(f"Protocol Sample Trace failed: {e}")


class ProtocolSpecialization(ProtocolArtifact):
    specialization: BehaviorSpecialization

    def __init__(self, specialization: BehaviorSpecialization) -> None:
        super().__init__()
        self.specialization = specialization

    def write_output(self, filename_prefix: str):
        pass

    def generate_artifact(self, harness: "ProtocolHarness"):
        try:
            results = self.specialization.data
            specialization_classname = self.specialization.__class__.__name__
            specialization_dir = os.path.join(
                harness.full_output_dir, specialization_classname
            )
            os.makedirs(specialization_dir, exist_ok=True)
            for i, result in enumerate(results):
                # extension = mimetypes.guess_extension(magic.Magic(mime=True).from_file(result))
                extension = "json"
                result_file = os.path.join(
                    specialization_dir,
                    f"{specialization_classname}_result_{i}.{extension}",
                )
                with open(result_file, "w") as f:
                    f.write(str(result))
            self.status = ProtocolArtifactStatus.PASS
            self.results["filename"] = specialization_dir
        except Exception as e:
            self.status = ProtocolArtifactStatus.FAIL
            self.results["exception"] = str(e)
            l.exception(f"Protocol Specialization {self.specialization} failed: {e}")


class ProtocolHarness:
    namespace: str = None
    protocol_name: str = None
    protocol_long_name: str = None
    protocol_version: str = None
    protocol_description: str = None
    entry_point: Callable
    artifacts: List[ProtocolArtifact] = None
    base_artifacts: List[ProtocolArtifact] = None
    output_dir: str = None
    base_dir: str = None
    full_output_dir: str = None
    libraries: List[str] = None
    parameter_values: List[ParameterValue] = None
    execution_id: str = None
    agent: Union[sbol3.Agent, str] = None
    execution_kwargs: Dict[str, Any] = None
    _results: Dict[str, Any] = None
    clean_output: bool = False

    def __init__(self, *args, **kwargs):
        self.namespace = (
            kwargs["namespace"] if "namespace" in kwargs else "https://labop.io/"
        )
        sbol3.set_namespace(self.namespace)
        self.protocol_name = (
            kwargs["protocol_name"] if "protocol_name" in kwargs else "default_name"
        )
        self.protocol_long_name = (
            kwargs["protocol_long_name"]
            if "protocol_long_name" in kwargs
            else "default name"
        )

        self.protocol_version = (
            kwargs["protocol_version"] if "protocol_version" in kwargs else "1.0"
        )

        self.protocol_description = (
            kwargs["protocol_description"]
            if "protocol_description" in kwargs
            else "default description"
        )

        self.clean_output = (
            kwargs["clean_output"] if "clean_output" in kwargs else self.clean_output
        )

        self.execution_kwargs = (
            kwargs["execution_kwargs"] if "execution_kwargs" in kwargs else {}
        )

        self.base_dir = kwargs["base_dir"] if "base_dir" in kwargs else "."
        self.output_dir = (
            kwargs["output_dir"] if "output_dir" in kwargs else "artifacts"
        )
        self.full_output_dir = os.path.join(self.base_dir, self.output_dir)

        # Store outputs in full_output_dir
        os.makedirs(self.full_output_dir, exist_ok=True)
        l.info(f"Writing protocol artifacts to: {self.full_output_dir}")

        self.entry_point = kwargs["entry_point"]
        self.artifacts = kwargs["artifacts"] if "artifacts" in kwargs else []

        self.libraries = (
            kwargs["libraries"]
            if "libraries" in kwargs
            else [
                "liquid_handling",
                "plate_handling",
                "spectrophotometry",
                "sample_arrays",
            ]
        )
        self.parameter_values = (
            kwargs["parameter_values"] if "parameter_values" in kwargs else []
        )
        self.execution_id = (
            kwargs["execution_id"] if "execution_id" in kwargs else self.execution_id
        )
        self.agent = (
            kwargs["agent"] if "agent" in kwargs else sbol3.Agent("labop_harness")
        )

        if "base_artifacts" in kwargs:
            self.base_artifacts = kwargs["base_artifacts"]
        else:
            protocol_artifact = ProtocolNTuples(
                namespace=self.namespace,
                protocol_name=self.protocol_name,
                protocol_long_name=self.protocol_long_name,
                protocol_version=self.protocol_version,
                protocol_description=self.protocol_description,
            )

            dataset_filename = os.path.join(
                self.full_output_dir, self.dataset_filename()
            )

            specializations = [
                a for a in self.artifacts if isinstance(a, ProtocolSpecialization)
            ]

            protocol_execution_artifact = ProtocolExecutionNTuples(
                protocol_artifact=protocol_artifact,
                agent=self.agent,
                execution_id=self.execution_id,
                parameter_values=self.parameter_values,
                specializations=specializations,
                dataset_filename=dataset_filename,
                execution_kwargs=self.execution_kwargs,
            )
            sample_traces = [
                a for a in self.artifacts if isinstance(a, ProtocolSampleTrace)
            ]
            if len(sample_traces) == 0:
                sample_traces = [
                    ProtocolSampleTrace(
                        protocol_execution_artifact=protocol_execution_artifact
                    )
                ]
            self.base_artifacts = (
                kwargs["base_artifacts"]
                if "base_artifacts" in kwargs
                else [
                    protocol_artifact,
                    ProtocolDiagram(protocol_artifact=protocol_artifact),
                    protocol_execution_artifact,
                    ProtocolExecutionDiagram(
                        protocol_execution_artifact=protocol_execution_artifact
                    ),
                ]
                + sample_traces
            )
            for a in self.artifacts:
                if isinstance(a, ProtocolRubric):
                    a.protocol_artifact = protocol_artifact
            for a in self.artifacts:
                if isinstance(a, ProtocolExecutionRubric):
                    a.protocol_execution_artifact = protocol_execution_artifact

        self.all_artifacts = self.base_artifacts + self.artifacts
        self._results = {}

    def filename_prefix(self) -> str:
        return self.entry_point.__name__

    def dataset_filename(self) -> str:
        return self.filename_prefix() + ".data.xslx"

    def artifacts_summary(self, verbose=False) -> str:
        summary = ""
        for a in self.base_artifacts + self.artifacts:
            summary += f"    - {a.__class__.__name__}"
            if verbose:
                summary += f": {a.configuration_summary(verbose=verbose)}\n"
            else:
                summary += "\n"
        summary = f"""
{'*'*80}

    LabOP Protocol Harness

    Configuration:
    --------------
    Artifacts:
{summary}
{'*'*80}
        """
        return summary

    def artifacts_results_summary(self, verbose=False) -> str:
        summary = ""
        for a in self.base_artifacts + self.artifacts:
            summary += f"    {'-'*76}\n    - {a.__class__.__name__} ({a.status}): \n"
            if verbose:
                summary += f"    {'-'*76}\n{a.results_summary()}\n"
        summary = f"""
{'*'*80}

    Harness Results Summary

    Artifacts:
{summary}
{'*'*80}
        """
        return summary

    def artifacts_of_type(self, artifact_type) -> List[ProtocolArtifact]:
        try:
            ea = [a for a in self.all_artifacts if isinstance(a, artifact_type)]
            return ea
        except Exception as e:
            l.exception(f"Could not find an artifacts of type {artifact_type}: {e}")
            raise e

    def run(self, verbose=False):
        self.initialize(verbose=verbose)
        self.main(verbose=verbose)
        self.finalize(verbose=verbose)

    def initialize(self, verbose=False):
        if self.clean_output:
            l.warn(f"Deleting contents of output directory: {self.full_output_dir}")
            for root, dirs, files in os.walk(self.full_output_dir):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
        l.info(self.artifacts_summary(verbose=verbose))

    def errors(self) -> List[ProtocolArtifact]:
        return [
            a for a in self.all_artifacts if a.status == ProtocolArtifactStatus.FAIL
        ]

    def main(self, verbose=False):
        artifact_order = [
            ProtocolNTuples,
            ProtocolRubric,
            ProtocolDiagram,
            ProtocolExecutionNTuples,
            ProtocolExecutionRubric,
            ProtocolExecutionDiagram,
            ProtocolSampleTrace,
            ProtocolSpecialization,
        ]
        for a_type in artifact_order:
            for a in self.artifacts_of_type(a_type):
                a.generate_artifact(self)

    def finalize(self, verbose=False):
        summary = self.artifacts_results_summary(verbose=verbose)

        l.info(summary)
        results_file = os.path.join(self.full_output_dir, "harness.out")
        with open(results_file, "w") as f:
            f.write(self.artifacts_results_summary(verbose=True))


class ProtocolLoader:
    filename: str = None
    entrypoint_name: str = None
    module = None

    def __init__(self, filename: str, entrypoint_name: str):
        self.filename = filename
        self.entrypoint_name = entrypoint_name

        self.module = self.load_module()

    def load_module(self):
        loader = SourceFileLoader(self.entrypoint_name, self.filename)
        spec = spec_from_loader(loader.name, loader)
        module = module_from_spec(spec)
        loader.exec_module(module)
        return module

    def generate_protocol(self, doc: sbol3.Document, protocol: Protocol) -> Protocol:
        entrypoint = getattr(self.module, self.entrypoint_name)
        return entrypoint(doc, protocol)
