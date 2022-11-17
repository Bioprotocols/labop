import os
from math import inf

import sbol3
import tyto


# See https://docs.opentrons.com/v2/new_pipette.html for pipette specifications

# TODO: factor out ContO.  This tyto ontology interface is duplicated
# here and in opentrons_specialization.py
container_ontology_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../labop/container-ontology.ttl')
ContO = tyto.Ontology(path=container_ontology_path, uri='https://sift.net/container-ontology/container-ontology')


labop_ns = 'http://bioprotocols.org/labop#'
container_ns = 'https://sift.net/container-ontology/container-ontology#'
sbol3.set_namespace(f'http://bioprotocols.org/labop/opentrons/')


class OT2Instrument(sbol3.Agent, sbol3.CustomTopLevel):
    """Specialized Agent class used for OT2 Hardware modules and Pipettes
    """

    def __init__(self, identity, type_uri=f'{labop_ns}OT2Instrument', **kwargs):
        super().__init__(identity=identity, type_uri=type_uri, **kwargs)


class OT2Pipette(OT2Instrument, sbol3.CustomTopLevel):
    """Specialized Agent class used for OT2 Pipettes
    """

    def __init__(self,
                 identity: str,
                 compatible_tips: list[str],
                 max_volume: sbol3.Measure,
                 type_uri=f'{labop_ns}OT2Pipette',
                 **kwargs):
        super().__init__(identity=identity, type_uri=type_uri, **kwargs)
        self.compatible_tips = sbol3.URIProperty(self, 
                                                 f'{labop_ns}isCompatibleWith',
                                                 1, inf,
                                                 initial_value=compatible_tips)
        self.max_volume = sbol3.OwnedObject(self,
                                            f'{labop_ns}maxVolume',
                                            1, 1,
                                            initial_value=max_volume)


def build_ot2_instrument(*, identity, type_uri):
    """A builder function to be called by the SBOL3 parser
    when it encounters a Component in an SBOL file.
    """

    # `types` is required and not known at build time.
    # Supply a missing value to the constructor, then clear
    # the missing value before returning the built object.
    obj = OT2Instrument(identity=identity,
                        type_uri=type_uri)
    return obj


def build_ot2_pipette(*, identity, type_uri):
    """A builder function to be called by the SBOL3 parser
    when it encounters a Component in an SBOL file.
    """

    # `types` is required and not known at build time.
    # Supply a missing value to the constructor, then clear
    # the missing value before returning the built object.
    obj = OT2Pipette(identity,
                     [sbol3.PYSBOL3_MISSING],
                     sbol3.Measure(0, sbol3.PYSBOL3_MISSING),
                     type_uri=type_uri)
    return obj



# Register the builder function so it can be invoked by
# the SBOL3 parser to build objects with a Component type URI
sbol3.Document.register_builder(f'{labop_ns}OT2Instrument',
                                build_ot2_instrument)


# Register the builder function so it can be invoked by
# the SBOL3 parser to build objects with a Component type URI
sbol3.Document.register_builder(f'{labop_ns}OT2Pipette',
                                build_ot2_pipette)


p10_single = OT2Pipette('p10_single',
           [ContO.Opentrons_96_Tip_Rack_10_µL, ContO.Opentrons_96_Filter_Tip_Rack_10_µL],
           sbol3.Measure(10, tyto.OM.microliter),
           name='P10 Single')
p10_multi = OT2Pipette('p10_multi',
           [ContO.Opentrons_96_Tip_Rack_10_µL, ContO.Opentrons_96_Filter_Tip_Rack_10_µL],
           sbol3.Measure(10, tyto.OM.microliter),
           name='P10 Multi')
p20_single_gen2 = OT2Pipette('p20_single_gen2',
           [ContO.Opentrons_96_Tip_Rack_20_µL, ContO.Opentrons_96_Filter_Tip_Rack_20_µL],
           sbol3.Measure(20, tyto.OM.microliter), 
           name='P20 Single GEN2')
p20_multi_gen2 = OT2Pipette('p20_multi_gen2',
           [ContO.Opentrons_96_Tip_Rack_20_µL, ContO.Opentrons_96_Filter_Tip_Rack_20_µL],
           sbol3.Measure(20, tyto.OM.microliter),
           name='P20 Multi GEN2')
p50_single = OT2Pipette('p50_single',
           [ContO.Opentrons_96_Tip_Rack_200_µL, ContO.Opentrons_96_Filter_Tip_Rack_200_µL],
           sbol3.Measure(50, tyto.OM.microliter),
           name='P50 Single')
p50_multi = OT2Pipette('p50_multi',
           [ContO.Opentrons_96_Tip_Rack_300_µL, ContO.Opentrons_96_Filter_Tip_Rack_300_µL],
           sbol3.Measure(50, tyto.OM.microliter),
           name='P50 Multi')
p300_single = OT2Pipette('p300_single',
           [ContO.Opentrons_96_Tip_Rack_300_µL, ContO.Opentrons_96_Filter_Tip_Rack_300_µL],
           sbol3.Measure(300, tyto.OM.microliter),
           name='P300 Single')
p300_single_gen2 = OT2Pipette('p300_single_gen2',
           [ContO.Opentrons_96_Tip_Rack_300_µL, ContO.Opentrons_96_Filter_Tip_Rack_300_µL],
           sbol3.Measure(300, tyto.OM.microliter),
           name='P300 Single GEN2')
p300_multi = OT2Pipette('p300_multi',
           [ContO.Opentrons_96_Tip_Rack_300_µL, ContO.Opentrons_96_Filter_Tip_Rack_300_µL],
           sbol3.Measure(300, tyto.OM.microliter),
           name='P300 Multi')
p300_multi_gen2 = OT2Pipette('p300_multi_gen2',
           [ContO.Opentrons_96_Tip_Rack_300_µL, ContO.Opentrons_96_Filter_Tip_Rack_300_µL],
           sbol3.Measure(300, tyto.OM.microliter),
           name='P300 Multi GEN2')
p1000_single = OT2Pipette('p1000_single',
           [ContO.Opentrons_96_Tip_Rack_1000_µL, ContO.Opentrons_96_Filter_Tip_Rack_1000_µL],
           sbol3.Measure(1000, tyto.OM.microliter),
           name='P1000 Single')
p1000_single_gen2 = OT2Pipette('p1000_single_gen2',
           [ContO.Opentrons_96_Tip_Rack_1000_µL, ContO.Opentrons_96_Filter_Tip_Rack_1000_µL],
           sbol3.Measure(1000, tyto.OM.microliter),
           name='P1000 Single GEN2')
temperature_module = OT2Instrument('temperature_module', name='Temperature Module GEN1'),
temperature_module_gen2 = OT2Instrument('temperature_module_gen2', name='Temperature Module GEN2'),
magdeck = OT2Instrument('magdeck', name='Magnetic Module GEN1'),
magnetic_module_gen2 = OT2Instrument('magnetic_module_gen2', name='Magnetic Module GEN2'),
thermocycler_module = OT2Instrument('thermocycler_module', name='Thermocycler Module'),


## Map terms in the Container ontology to OT2 API names
LABWARE_MAP = {
    'cont:Opentrons96TipRack10uL': 'opentrons_96_tiprack_10ul',
    'cont:Opentrons96TipRack300uL': 'opentrons_96_tiprack_300ul',
    'cont:Opentrons96TipRack1000uL': 'opentrons_96_tiprack_1000ul',
    'cont:Opentrons96FilterTipRack10uL': 'opentrons_96_filtertiprack_10ul',
    'cont:Opentrons96FilterTipRack200uL': 'opentrons_96_filtertiprack_200ul',
    'cont:Opentrons96FilterTipRack1000uL': 'opentrons_96_filtertiprack_1000ul',
    'cont:Opentrons24TubeRackwithEppendorf1.5mLSafe-LockSnapcap': 'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap',
    'cont:Corning96WellPlate360uLFlat': 'corning_96_wellplate_360ul_flat',
    'cont:Biorad96WellPCRPlate': 'biorad_96_wellplate_200ul_pcr',
}

REVERSE_LABWARE_MAP = LABWARE_MAP.__class__(map(reversed, LABWARE_MAP.items()))

EQUIPMENT = {
    'p20_single_gen2': p20_single_gen2,
    'p300_single_gen2': p300_single_gen2,
    'p1000_single_gen2': p1000_single_gen2,
    'p300_multi_gen2': p300_multi_gen2,
    'p20_multi_gen2': p20_multi_gen2,
    'p10_single': p10_single,
    'p10_multi': p10_multi,
    'p50_single': p50_single,
    'p50_multi': p50_multi,
    'p300_single': p300_single,
    'p300_multi': p300_multi,
    'p1000_single': p1000_single,
    'temperature_module': temperature_module,
    'tempdeck': temperature_module,
    'temperature_module_gen2': temperature_module_gen2,
    'magnetic_module': magdeck,
    'magnetic_module_gen2': magnetic_module_gen2,
    'thermocycler_module': thermocycler_module,
    'thermocycler': thermocycler_module
}

# This sets a condition by which add_call_behavior_action
# will be forced to use copies of these Agent objects
doc = sbol3.Document()
for eq in EQUIPMENT.values():
    doc.add(eq)
