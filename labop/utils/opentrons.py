import io
import opentrons.simulate as simulate
from opentrons.protocols import bundle
import sys


def run_ot2_sim(filename):
    sys.argv = []
    """Run the simulation"""
    # parser = argparse.ArgumentParser(
    #     prog="opentrons_simulate", description="Simulate an OT-2 protocol"
    # )
    # parser = simulate.get_arguments(parser)

    # args = parser.parse_args()
    # Try to migrate api v1 containers if needed

    # duration_estimator = DurationEstimator() if args.estimate_duration else None  # type: ignore[no-untyped-call]
    duration_estimator = None

    with open(filename, "r") as protocol:
        runlog, maybe_bundle = simulate.simulate(
            protocol,
            # args.protocol.name,
            # getattr(args, "custom_labware_path", []),
            # getattr(args, "custom_data_path", []) + getattr(args, "custom_data_file", []),
            # duration_estimator=duration_estimator,
            # hardware_simulator_file_path=getattr(args, "custom_hardware_simulator_file"),
            # log_level=args.log_level,
        )

    if maybe_bundle:
        bundle_name = "bundle"  # getattr(args, "bundle", None)
        # if bundle_name == args.protocol.name:
        #     raise RuntimeError("Bundle path and input path must be different")
        bundle_dest = simulate._get_bundle_dest(
            bundle_name, "PROTOCOL.ot2.zip", "my_protocol"  # args.protocol.name
        )
        if bundle_dest:
            bundle.create_bundle(maybe_bundle, bundle_dest)

    # if args.output == "runlog":
    print(simulate.format_runlog(runlog))

    if duration_estimator:
        duration_seconds = duration_estimator.get_total_duration()
        hours = int(duration_seconds / 60 / 60)
        minutes = int((duration_seconds % (60 * 60)) / 60)
        print("--------------------------------------------------------------")
        print(f"Estimated protocol duration: {hours}h:{minutes}m")
        print("--------------------------------------------------------------")
        print("WARNING: Protocol duration estimation is an experimental feature")

    return runlog


def make_demo_script(filename):
    protocol = io.StringIO()

    script = """
from opentrons import protocol_api

# metadata
metadata = {
    'protocolName': 'My Protocol',
    'author': 'Name <opentrons@example.com>',
    'description': 'Simple protocol to get started using the OT-2',
    'apiLevel': '2.12'
}



# protocol run function
def run(protocol: protocol_api.ProtocolContext):

    # labware
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', location='1')
    tiprack = protocol.load_labware('opentrons_96_tiprack_300ul', location='2')

    # pipettes
    left_pipette = protocol.load_instrument(
        'p300_single', mount='left', tip_racks=[tiprack])

    # commands
    left_pipette.pick_up_tip()
    left_pipette.aspirate(100, plate['A1'])
    left_pipette.dispense(100, plate['B2'])
    left_pipette.drop_tip()
"""
    protocol.write(script)

    with open(filename, "w") as f:
        f.write(protocol.getvalue())
    return filename
