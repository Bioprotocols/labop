from opentrons import protocol_api

metadata = {
    "apiLevel": "2.11",
    "description": "None",
    "protocolName": "Opentrons PCR Demo",
}


def run(protocol: protocol_api.ProtocolContext):
    p300_single = protocol.load_instrument("p300_single", "left")
    thermocycler_module = protocol.load_module("thermocycler module", "7")
    thermocycler_module.open_lid()
    labware4 = protocol.load_labware("opentrons_96_tiprack_300ul", "4")
    p300_single.tip_racks.append(labware4)
    labware2 = protocol.load_labware(
        "opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", "2"
    )
    labware1 = protocol.load_labware("corning_96_wellplate_360ul_flat", "1")
    labware3 = protocol.load_labware("corning_96_wellplate_360ul_flat", "3")
    labware7 = thermocycler_module.load_labware("biorad_96_wellplate_200ul_pcr")
    p300_single.transfer(9.0, labware2["B1"], labware7["A1"])  # Add water
    p300_single.transfer(1.0, labware1["A1"], labware7["A1"])  # Add F primer
    p300_single.transfer(1.0, labware1["A3"], labware7["A1"])  # Add R primer
    p300_single.transfer(1.0, labware3["A1"], labware7["A1"])  # Add template
    p300_single.transfer(12.5, labware2["A1"], labware7["A1"])  # Add 2X master mix
    p300_single.transfer(9.0, labware2["B1"], labware7["A2"])  # Add water
    p300_single.transfer(1.0, labware1["A2"], labware7["A2"])  # Add F primer
    p300_single.transfer(1.0, labware1["A4"], labware7["A2"])  # Add R primer
    p300_single.transfer(1.0, labware3["A1"], labware7["A2"])  # Add template
    p300_single.transfer(12.5, labware2["A1"], labware7["A2"])  # Add 2X master mix
    p300_single.transfer(9.0, labware2["B1"], labware7["A3"])  # Add water
    p300_single.transfer(1.0, labware1["A1"], labware7["A3"])  # Add F primer
    p300_single.transfer(1.0, labware1["A3"], labware7["A3"])  # Add R primer
    p300_single.transfer(1.0, labware3["A3"], labware7["A3"])  # Add template
    p300_single.transfer(12.5, labware2["A1"], labware7["A3"])  # Add 2X master mix
    p300_single.transfer(9.0, labware2["B1"], labware7["A4"])  # Add water
    p300_single.transfer(1.0, labware1["A2"], labware7["A4"])  # Add F primer
    p300_single.transfer(1.0, labware1["A4"], labware7["A4"])  # Add R primer
    p300_single.transfer(1.0, labware3["A3"], labware7["A4"])  # Add template
    p300_single.transfer(12.5, labware2["A1"], labware7["A4"])  # Add 2X master mix
    thermocycler_module.close_lid()
    profile = [
        {"temperature": 98.0, "hold_time_seconds": 10.0},
        {"temperature": 45.0, "hold_time_seconds": 45.0},
        {"temperature": 65.0, "hold_time_seconds": 60.0},
    ]
    thermocycler_module.execute_profile(steps=profile, repetitions=30)
    thermocycler_module.set_block_temperature(4)
