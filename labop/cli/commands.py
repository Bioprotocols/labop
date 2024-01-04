import argparse
import logging

from labop.cli.utils import project_next_suffix, project_prefix

l = logging.Logger(__file__)
l.setLevel(logging.INFO)


class CommandDefaultParameters:
    DEFAULT_PROJECT_NAME: str = "labop-quick-start-project-001"


def cmd_quick_start(project_name: str):
    # Create a directory
    if os.path.exists(project_name):
        next_project_name = (
            f"{project_prefix(project_name)}-{project_next_suffix(project_name)}"
        )
        l.debug(f"{project_name} exists, creating {next_project_name} ...")
        project_name = next_project_name

    # Make protocol script
    protocol_script = quick_start_script(project_name)


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


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("protocol-script")
    parser.add_argument(
        "-q",
        "--quick-start",
        default=CommandDefaultParameters.DEFAULT_PROJECT_NAME,
        action="store_const",
        help=f"Generate a quick-start protocol project in the specified directory.",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="./artifacts",
        action="store_const",
        help="Output Directory",
    )

    parser.add_argument(
        "-g",
        "--generate-protocol",
        default=False,
        action="store_true",
        help=f"Generate the RDF n-tuples (.nt) LabOP protocol file.",
    )
    parser.add_argument(
        "-c",
        "--compute-sample-trajectory",
        default=False,
        action="store_true",
        help=f"Execute the protocol to generate the sample trajectory of the LabOP protocol.",
    )
    parser.add_argument(
        "-m",
        "--generate-markdown",
        default=False,
        action="store_true",
        help=f"Execute the protocol to generate the Markdown (.md) version of the LabOP protocol.",
    )
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


def main():
    args = get_args()
    process_arguments(args)


if __name__ == "__main__":
    main()
