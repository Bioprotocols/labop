import argparse
import logging
import os
import sys
from functools import partial

from .utils import project_next_suffix, project_prefix


def set_level(level: int):
    logging.getLogger().setLevel(level)
    handlers = logging.getLogger().handlers
    for h in handlers:
        h.setLevel(level)


def add_handler():
    logging.basicConfig(stream=sys.stdout)
    ch = logging.StreamHandler(sys.stdout)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logging.getLogger().handlers = [ch]


class CommandDefaultParameters:
    DEFAULT_PROJECT_NAME: str = "labop-quick-start-project-001"


def cmd_quick_start(project_name: str, base_dir: str = "."):
    # Create a directory
    if os.path.exists(os.path.join(base_dir, project_name)):
        next_project_name = (
            f"{project_prefix(project_name)}-{project_next_suffix(project_name)}"
        )
        l.debug(f"{project_name} exists, creating {next_project_name} ...")
        project_name = next_project_name

    # Setup directory
    os.makedirs(os.path.join(base_dir, project_name, "artifacts"))

    # Make protocol script
    protocol_script = make_quick_start_script(project_name)
    with open(os.path.join(base_dir, project_name, f"{project_name}.py"), "w") as f:
        f.write(protocol_script)


def make_quick_start_script(project_name):
    msg = f"Generating protocol: {project_name}"
    return f"""
import sbol3
from labop import Protocol

def generate_protocol(doc: sbol3.Document, protocol: Protocol) -> Protocol:
    print("{msg}")
    return protocol
"""


def process_arguments(args):
    if args.quick_start:
        cmd_quick_start(args.quick_start)

    # if args.generate_protocol or not os.path.exists(
    #     os.path.join(OUT_DIR, filename + "-protocol.nt")
    # ):
    #     print("Generating Protocol ...")
    #     protocol, doc = generate_protocol()

    # if args.compute_sample_trajectory:
    #     compute_sample_trajectory(*read_protocol())

    # if args.generate_markdown:
    #     print("Generating Markdown ...")
    #     generate_markdown_specialization(*read_protocol())

    # if args.generate_autoprotocol:
    #     print("Generating Autoprotocol ...")
    #     generate_autoprotocol_specialization(*read_protocol())

    # if args.test_autoprotocol:
    #     print("Submitting Autoprotocol Test Run ...")
    #     proceed = input("Proceed? y/[n]")
    #     # proceed = "y"
    #     if proceed and proceed == "y":
    #         test_autoprotocol()

    # if args.generate_emeraldcloud:
    #     print("Generating EmeraldCloud ...")
    #     generate_emeraldcloud_specialization(*read_protocol())


def quickstart(args):
    cmd_quick_start(args.projectname)


def get_quickstart_args(subparsers):
    parser = subparsers.add_parser(
        "quickstart",
        description="create a demo protocol project in ./PROJECT_NAME",
        help="create a demo protocol project",
    )
    parser.add_argument(
        "-p",
        "--projectname",
        type=str,
        metavar="PROJECT_NAME",
        default=CommandDefaultParameters.DEFAULT_PROJECT_NAME,
        help="name of the project",
    )
    parser.set_defaults(func=quickstart)


def protocol_name(args):
    return sanitize_protocol_name(args.projectname)


def protocol_long_name(args):
    return args.projectname


def create_protocol(protocol_def_file, doc, protocol):
    from labop.execution.harness import ProtocolLoader

    protocol = ProtocolLoader(protocol_def_file, "generate_protocol").generate_protocol(
        doc, protocol
    )
    return protocol


def sanitize_protocol_name(name: str) -> str:
    return name.replace(" ", "_").replace("-", "_").replace(":", "_").replace(".", "_")


def compile_protocol_artifact(args):
    from labop.execution.harness import ProtocolNTuples

    return ProtocolNTuples(
        namespace="https://labop.io/",
        protocol_name=protocol_name(args),
        protocol_long_name=protocol_long_name(args),
        protocol_version="1.0",
        protocol_description=args.projectname,
    )


def load_protocol(args):
    from labop.execution.harness import ProtocolNTuples

    return ProtocolNTuples(
        namespace="https://labop.io/",
        protocol_name=protocol_name(args),
        protocol_long_name=protocol_long_name(args),
        protocol_version="1.0",
        protocol_description=args.projectname,
        cached_protocol_file=cached_protocol_file(args),
    )


def protocol_execution_artifact(protocol_artifact, specializations=[]):
    from labop.execution.harness import ProtocolExecutionNTuples

    return ProtocolExecutionNTuples(
        protocol_artifact=protocol_artifact,
        # agent=self.agent,
        # execution_id=self.execution_id,
        parameter_values=[],
        specializations=specializations,
        # dataset_filename=dataset_filename,
        # execution_kwargs=self.execution_kwargs,
    )


def protocol_script(args):
    return os.path.join(args.projectname, f"{args.projectname}.py")


def cached_protocol_file(args):
    return os.path.join(args.projectname, "artifacts", protocol_name(args) + ".nt")


def protocol_harness(args, artifacts):
    from labop.execution.harness import ProtocolHarness

    l.debug(f"Harness output_dir = {output_dir(args)}")
    return ProtocolHarness(
        output_dir=output_dir(args),
        protocol_name=protocol_name(args),
        protocol_long_name=protocol_long_name(args),
        entry_point=partial(create_protocol, protocol_script(args)),
        base_artifacts=artifacts,
    )


def output_dir(args):
    return os.path.join(args.projectname, "artifacts")


def ensure_project_exists(args):
    if not os.path.exists(args.projectname):
        l.warn(f"Cannot run command on project that does not exist: {args.projectname}")
        do_quickstart = input("Create quickstart protocol [Y/n]? ")
        if do_quickstart.lower() == "y" or do_quickstart == "":
            quickstart(args)
        else:
            return False
    return True


def ensure_protocol_exists(args):
    if not os.path.exists(cached_protocol_file(args)):
        l.warn(
            f"Cannot run command because the compiled protocol does not exist: {args.projectname}"
        )
        do_compile = input("Compile protocol [Y/n]? ")
        if do_compile.lower() == "y" or do_compile == "":
            compile(args)
        else:
            return False
    return True


def ensure_execution_exists(args):
    import sbol3

    from labop import ProtocolExecution

    doc = sbol3.Document()
    doc.read(cached_protocol_file(args))
    # executions = doc.find_all(lambda x: isinstance(x, ProtocolExecution))
    execution = doc.find(args.execution)
    if execution is None:
        l.error(f"Cannot remove execution {args.execution} because it does not exist.")
        return False
    else:
        return True


def compile(args):
    if ensure_project_exists(args):
        l.debug(f"compile: {args.projectname}")
        protocol_artifact = compile_protocol_artifact(args)
        harness = protocol_harness(args, [protocol_artifact])
        harness.run()


def diagram(args):
    if ensure_project_exists(args) and ensure_protocol_exists(args):
        l.debug(f"diagram: {args.projectname}")
        from labop.execution.harness import ProtocolDiagram

        protocol_artifact = load_protocol(args)
        protocol_diagram = ProtocolDiagram(protocol_artifact=protocol_artifact)
        harness = protocol_harness(args, [protocol_artifact, protocol_diagram])
        harness.run()


def execute_run(args):
    l.debug(f"execute run: {args.projectname}")
    if ensure_project_exists(args) and ensure_protocol_exists(args):
        protocol_artifact = load_protocol(args)
        protocol_execution = protocol_execution_artifact(protocol_artifact)
        harness = protocol_harness(args, [protocol_artifact, protocol_execution])
        harness.run()


def execute_list(args):
    l.debug(f"execute list: {args}")
    if ensure_project_exists(args) and ensure_protocol_exists(args):
        import sbol3

        from labop import ProtocolExecution

        doc = sbol3.Document()
        doc.read(cached_protocol_file(args))
        executions = doc.find_all(lambda x: isinstance(x, ProtocolExecution))
        if len(executions) > 0:
            l.info("Executions:")
            l.info("\n".join([ex.identity for ex in executions]))
        else:
            l.info("Could not find any executions")
        # print({o.identity: o for o in doc.objects})


def execute_rm(args):
    l.debug(f"execute remove: {args}")
    if (
        ensure_project_exists(args)
        and ensure_protocol_exists(args)
        and ensure_execution_exists(args)
    ):
        rm_execution = input(
            "Found execution, are you sure you want to remove it? [N/y] "
        )
        if rm_execution.lower() == "y":
            import sbol3

            from labop import (
                BehaviorExecution,
                CallBehaviorExecution,
                ProtocolExecution,
            )

            doc = sbol3.Document()
            doc.read(cached_protocol_file(args))
            execution: ProtocolExecution = doc.find(args.execution)
            behavior_executions: List[BehaviorExecution] = [
                ex.get_call()
                for ex in execution.executions
                if isinstance(ex, CallBehaviorExecution)
            ]
            doc.remove([execution] + behavior_executions)
            # print({o.identity: o for o in doc.objects})
            with open(cached_protocol_file(args), "w") as f:
                f.write(doc.write_string(sbol3.SORTED_NTRIPLES).strip())
            l.info(f"Successfully removed execution: {args.execution}")
        else:
            l.info(f"Aborting removal of execution: {args.execution}")


def markdown_specialization(args):
    if ensure_project_exists(args) and ensure_protocol_exists(args):
        l.debug(f"specialize markdown: {args.projectname}")
        protocol_artifact = load_protocol(args)
        from labop.execution.harness import ProtocolSpecialization
        from labop_convert.markdown import MarkdownSpecialization

        specialization = ProtocolSpecialization(
            specialization=MarkdownSpecialization("test_LUDOX_markdown.md")
        )
        protocol_execution = protocol_execution_artifact(
            protocol_artifact, [specialization]
        )
        harness = protocol_harness(args, [protocol_artifact, protocol_execution])
        harness.run()


def get_compile_args(subparsers):
    parser = subparsers.add_parser(
        "compile", help="generate an n-tuples file for a project"
    )
    parser.add_argument("projectname", type=str, help="name of the project")
    parser.set_defaults(func=compile)


def get_diagram_args(subparsers):
    parser = subparsers.add_parser("diagram", help="generate a diagram of a protocol")
    parser.add_argument("projectname", type=str, help="name of the project")
    parser.set_defaults(func=diagram)


def get_execution_args(parsers):
    parser = parsers.add_parser("execute", help="execute a protocol")

    subparsers = parser.add_subparsers(
        title="subcommands",
        description="execute subcommands",
        help="execute subcommands",
    )
    list_parser = subparsers.add_parser("list", help="list executions")
    list_parser.set_defaults(func=execute_list)
    list_parser.add_argument("projectname", type=str, help="name of the project")

    run_parser = subparsers.add_parser("run", help="run new execution")
    run_parser.add_argument("projectname", type=str, help="name of the project")
    run_parser.set_defaults(func=execute_run)

    rm_parser = subparsers.add_parser("remove", help="remove execution")
    rm_parser.add_argument("projectname", type=str, help="name of the project")
    rm_parser.add_argument("execution", type=str, help="id of the execution")
    rm_parser.set_defaults(func=execute_rm)


def get_specialize_args(parsers):
    parser = parsers.add_parser("specialize", help="specialize a protocol")

    subparsers = parser.add_subparsers(
        title="specializations",
        description="labop specializations",
        help="available specializations",
    )
    get_markdown_specialization(subparsers)


def get_markdown_specialization(subparsers):
    parser = subparsers.add_parser("markdown", help="specialize a protocol as markdown")
    parser.add_argument("projectname", type=str, help="name of the project")
    parser.set_defaults(func=markdown_specialization)


def get_args():
    parser = argparse.ArgumentParser(prog="labop")

    subparsers = parser.add_subparsers(
        title="subcommands",
        description="labop subcommands",
        help="available subcommands",
    )

    get_quickstart_args(subparsers)
    get_compile_args(subparsers)
    get_diagram_args(subparsers)
    get_execution_args(subparsers)
    get_specialize_args(subparsers)

    # parser.add_argument(
    #     "-g",
    #     "--generate-protocol",
    #     default=False,
    #     action="store_true",
    #     help=f"Generate the RDF n-tuples (.nt) LabOP protocol file.",
    # )
    # parser.add_argument(
    #     "-c",
    #     "--compute-sample-trajectory",
    #     default=False,
    #     action="store_true",
    #     help=f"Execute the protocol to generate the sample trajectory of the LabOP protocol.",
    # )
    # parser.add_argument(
    #     "-m",
    #     "--generate-markdown",
    #     default=False,
    #     action="store_true",
    #     help=f"Execute the protocol to generate the Markdown (.md) version of the LabOP protocol.",
    # )
    # parser.add_argument(
    #     "-a",
    #     "--generate-autoprotocol",
    #     default=False,
    #     action="store_true",
    #     help=f"Execute the protocol to generate the Autoprotocol version of the LabOP protocol.",
    # )

    # parser.add_argument(
    #     "-t",
    #     "--test-autoprotocol",
    #     default=False,
    #     action="store_true",
    #     help=f"Submit the artifacts/{filename}-autoprotocol.json Autoprotocol file to the Strateos run queue.",
    # )
    # parser.add_argument(
    #     "-e",
    #     "--generate-emeraldcloud",
    #     default=True,
    #     action="store_true",
    #     help=f"Execute the protocol to generate the Emerald Cloud Lab Mathmatica version of the LabOP protocol",
    # )
    args = parser.parse_args()
    return args


l = logging.Logger(__file__)
# l.setLevel(logging.INFO)


def main():

    add_handler()
    set_level(logging.INFO)
    l.info("HI")
    args = get_args()
    args.func(args)
    # process_arguments(args)


if __name__ == "__main__":
    main()
