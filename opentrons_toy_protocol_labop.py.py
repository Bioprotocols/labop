from opentrons import protocol_api

metadata = {
    "apiLevel": "2.11",
    "description": "Example Opentrons Protocol as LabOP",
    "protocolName": "OT2 simple toy demonstration",
}


def run(protocol: protocol_api.ProtocolContext):
    labware1 = protocol.load_labware("corning_96_wellplate_360ul_flat", "1")
    labware2 = protocol.load_labware("opentrons_96_tiprack_300ul", "2")
    p300_single = protocol.load_instrument("p300_single", "left")
    p300_single.tip_racks.append(labware2)
    p300_single.transfer(
        100.0, labware1["A1"], labware1["B2"]
    )  # Transfer ActivityNode name is not defined.
