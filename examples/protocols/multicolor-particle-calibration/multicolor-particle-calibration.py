'''
http://2018.igem.org/wiki/images/0/09/2018_InterLab_Plate_Reader_Protocol.pdf
'''
import os

import labop
import sbol3
import json
import xarray as xr
import pandas as pd

from tyto import OM
from labop.execution_engine import ExecutionEngine
from labop_convert.markdown.markdown_specialization import MarkdownSpecialization

from labop_convert.plate_coordinates import get_sample_list


doc = sbol3.Document()
sbol3.set_namespace('http://igem.org/engineering/')

#############################################
# Import the primitive libraries
print('Importing libraries')
labop.import_library('liquid_handling')
print('... Imported liquid handling')
labop.import_library('plate_handling')
print('... Imported plate handling')
labop.import_library('spectrophotometry')
print('... Imported spectrophotometry')
labop.import_library('sample_arrays')
print('... Imported sample arrays')


# create the materials to be provisioned
ddh2o = sbol3.Component('ddH2O', 'https://identifiers.org/pubchem.substance:24901740')
ddh2o.name = 'Water, sterile-filtered, BioReagent, suitable for cell culture'

silica_beads = sbol3.Component('silica_beads', 'https://nanocym.com/wp-content/uploads/2018/07/NanoCym-All-Datasheets-.pdf')
silica_beads.name = 'NanoCym 950 nm monodisperse silica nanoparticles'
silica_beads.description = '3e9 NanoCym microspheres/mL ddH20'  # where does this go?

pbs = sbol3.Component('pbs', 'https://pubchem.ncbi.nlm.nih.gov/substance/329753341')
pbs.name = 'Phosphate Buffered Saline'

fluorescein = sbol3.Component('fluorescein', 'https://pubchem.ncbi.nlm.nih.gov/substance/329753341')
fluorescein.name = 'Fluorescein'

cascade_blue = sbol3.Component('cascade_blue', 'https://pubchem.ncbi.nlm.nih.gov/substance/329753341')
cascade_blue.name = 'Cascade Blue'

sulforhodamine = sbol3.Component('sulforhodamine', 'https://pubchem.ncbi.nlm.nih.gov/substance/329753341')
sulforhodamine.name = 'Sulforhodamine'

doc.add(ddh2o)
doc.add(silica_beads)
doc.add(pbs)
doc.add(fluorescein)
doc.add(cascade_blue)
doc.add(sulforhodamine)


protocol = labop.Protocol('interlab')
protocol.name = 'Multicolor fluorescence per bacterial particle calibration'
protocol.version = '1.1b'
protocol.description = '''Plate readers report fluorescence values in arbitrary units that vary widely from instrument to instrument. Therefore absolute fluorescence values cannot be directly compared from one instrument to another. In order to compare fluorescence output of biological devices, it is necessary to create a standard fluorescence curve. This variant of the protocol uses two replicates of three colors of dye, plus beads.
Adapted from [https://dx.doi.org/10.17504/protocols.io.bht7j6rn](https://dx.doi.org/10.17504/protocols.io.bht7j6r) and [https://dx.doi.org/10.17504/protocols.io.6zrhf56](https://dx.doi.org/10.17504/protocols.io.6zrhf56)'''
doc.add(protocol)




# Provision an empty Microfuge tube in which to mix the standard solution

fluorescein_standard_solution_container = protocol.primitive_step('EmptyContainer',
                                                                  specification=labop.ContainerSpec('fluroscein_calibrant',
            name='Fluorescein calibrant',
                                                                                                   queryString='cont:StockReagent',
                                                                                                   prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))


sulforhodamine_standard_solution_container = protocol.primitive_step('EmptyContainer',
                                                                  specification=labop.ContainerSpec('sulforhodamine_calibrant',
            name='Sulforhodamine 101 calibrant',
                                                                                                   queryString='cont:StockReagent',
                                                                                                   prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))

cascade_blue_standard_solution_container = protocol.primitive_step('EmptyContainer',
                                                                  specification=labop.ContainerSpec('cascade_blue_calibrant',
            name='Cascade blue calibrant',
                                                                                                   queryString='cont:StockReagent',
                                                                                                   prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))

microsphere_standard_solution_container = protocol.primitive_step('EmptyContainer',
                                                                  specification=labop.ContainerSpec('microspheres',
            name='NanoCym 950 nm microspheres',
                                                                                                   queryString='cont:StockReagent',
                                                                                                   prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))




### Suspend calibrant dry reagents
suspend_fluorescein = protocol.primitive_step('Transfer',
                                   source=pbs,
                                   destination=fluorescein_standard_solution_container.output_pin('samples'),
                                   amount=sbol3.Measure(1, OM.millilitre))
suspend_fluorescein.description = f'The reconstituted `{fluorescein.name}` should have a final concentration of 10 uM in `{pbs.name}`'

vortex_fluorescein = protocol.primitive_step('Vortex',
                                             samples=fluorescein_standard_solution_container.output_pin('samples'),
                                             duration=sbol3.Measure(30, OM.second))

suspend_sulforhodamine = protocol.primitive_step('Transfer',
                                   source=pbs,
                                   destination=sulforhodamine_standard_solution_container.output_pin('samples'),
                                   amount=sbol3.Measure(1, OM.millilitre))
suspend_sulforhodamine.description = f'The reconstituted `{sulforhodamine.name}` standard will have a final concentration of 2 uM in `{pbs.name}`'

vortex_sulforhodamine = protocol.primitive_step('Vortex',
                                             samples=sulforhodamine_standard_solution_container.output_pin('samples'),
                                             duration=sbol3.Measure(30, OM.second))

suspend_cascade_blue = protocol.primitive_step('Transfer',
                                   source=ddh2o,
                                   destination=cascade_blue_standard_solution_container.output_pin('samples'),
                                   amount=sbol3.Measure(1, OM.millilitre))
suspend_cascade_blue.description = f'The reconstituted `{cascade_blue.name}` calibrant will have a final concentration of 10 uM in `{ddh2o.name}`.'

vortex_cascade_blue = protocol.primitive_step('Vortex',
                                             samples=cascade_blue_standard_solution_container.output_pin('samples'),
                                             duration=sbol3.Measure(30, OM.second))

suspend_silica_beads = protocol.primitive_step('Transfer',
                                   source=ddh2o,
                                   destination=microsphere_standard_solution_container.output_pin('samples'),
                                   amount=sbol3.Measure(1, OM.millilitre))
suspend_silica_beads.description = f'The resuspended `{silica_beads.name}` will have a final concentration of 3e9 microspheres/mL in `{ddh2o.name}`.'
vortex_silica_beads= protocol.primitive_step('Vortex',
                                             samples=microsphere_standard_solution_container.output_pin('samples'),
                                             duration=sbol3.Measure(30, OM.second))



# Transfer to plate
calibration_plate = protocol.primitive_step('EmptyContainer',
                                                                  specification=labop.ContainerSpec('calibration_plate',
            name='calibration plate',
                                                                                                   queryString='cont:Plate96Well',
                                                                                                   prefixMap={'cont': 'https://sift.net/container-ontology/container-ontology#'}))


fluorescein_wells_A1 = protocol.primitive_step('PlateCoordinates',
                                               source=calibration_plate.output_pin('samples'),
                                               coordinates='A1')
fluorescein_wells_B1 = protocol.primitive_step('PlateCoordinates',
                                               source=calibration_plate.output_pin('samples'),
                                               coordinates='B1')

sulforhodamine_wells_C1 = protocol.primitive_step('PlateCoordinates',
                                                  source=calibration_plate.output_pin('samples'),
                                                  coordinates='C1')
sulforhodamine_wells_D1 = protocol.primitive_step('PlateCoordinates',
                                                  source=calibration_plate.output_pin('samples'),
                                                  coordinates='D1')

cascade_blue_wells_E1 = protocol.primitive_step('PlateCoordinates',
                                                source=calibration_plate.output_pin('samples'),
                                                coordinates='E1')
cascade_blue_wells_F1 = protocol.primitive_step('PlateCoordinates',
                                                source=calibration_plate.output_pin('samples'),
                                                coordinates='F1')

silica_beads_wells_G1 = protocol.primitive_step('PlateCoordinates',
                                                source=calibration_plate.output_pin('samples'),
                                                coordinates='G1')
silica_beads_wells_H1 = protocol.primitive_step('PlateCoordinates',
                                                source=calibration_plate.output_pin('samples'),
                                                coordinates='H1')

# Plate blanks
blank_wells1 = protocol.primitive_step('PlateCoordinates',
                                                source=calibration_plate.output_pin('samples'),
                                                coordinates='A12:D12')
blank_wells2 = protocol.primitive_step('PlateCoordinates',
                                                source=calibration_plate.output_pin('samples'),
                                                coordinates='E12:H12')
transfer_blanks1 = protocol.primitive_step('Transfer',
                                      source=pbs,
                                      destination=blank_wells1.output_pin('samples'),
                                      amount=sbol3.Measure(100, OM.microlitre))
transfer_blanks1.description = ' These are blanks.'
transfer_blanks2 = protocol.primitive_step('Transfer',
                                      source=ddh2o,
                                      destination=blank_wells2.output_pin('samples'),
                                      amount=sbol3.Measure(100, OM.microlitre))
transfer_blanks2.description = ' These are blanks.'

### Plate calibrants in first column
transfer1 = protocol.primitive_step('Transfer',
                                      source=vortex_fluorescein.output_pin('mixed_samples'),
                                      destination=fluorescein_wells_A1.output_pin('samples'),
                                      amount=sbol3.Measure(200, OM.microlitre))
transfer2 = protocol.primitive_step('Transfer',
                                   source=vortex_fluorescein.output_pin('mixed_samples'),
                                   destination=fluorescein_wells_B1.output_pin('samples'),
                                   amount=sbol3.Measure(200, OM.microlitre))
transfer3 = protocol.primitive_step('Transfer',
                                   source=vortex_sulforhodamine.output_pin('mixed_samples'),
                                   destination=sulforhodamine_wells_C1.output_pin('samples'),
                                   amount=sbol3.Measure(200, OM.microlitre))
transfer4 = protocol.primitive_step('Transfer',
                                   source=vortex_sulforhodamine.output_pin('mixed_samples'),
                                   destination=sulforhodamine_wells_D1.output_pin('samples'),
                                   amount=sbol3.Measure(200, OM.microlitre))
transfer5 = protocol.primitive_step('Transfer',
                                    source=vortex_cascade_blue.output_pin('mixed_samples'),
                                    destination=cascade_blue_wells_E1.output_pin('samples'),
                                    amount=sbol3.Measure(200, OM.microlitre))
transfer6 = protocol.primitive_step('Transfer',
                                    source=vortex_cascade_blue.output_pin('mixed_samples'),
                                    destination=cascade_blue_wells_F1.output_pin('samples'),
                                    amount=sbol3.Measure(200, OM.microlitre))
transfer7 = protocol.primitive_step('Transfer',
                                    source=vortex_silica_beads.output_pin('mixed_samples'),
                                    destination=silica_beads_wells_G1.output_pin('samples'),
                                    amount=sbol3.Measure(200, OM.microlitre))

transfer8 = protocol.primitive_step('Transfer',
                                    source=vortex_silica_beads.output_pin('mixed_samples'),
                                    destination=silica_beads_wells_H1.output_pin('samples'),
                                   amount=sbol3.Measure(200, OM.microlitre))



dilution_series1 = protocol.primitive_step('PlateCoordinates',
                                           source=calibration_plate.output_pin('samples'),
                                           coordinates='A1:A11')

dilution_series2 = protocol.primitive_step('PlateCoordinates',
                                           source=calibration_plate.output_pin('samples'),
                                           coordinates='B1:B11')

dilution_series3 = protocol.primitive_step('PlateCoordinates',
                                           source=calibration_plate.output_pin('samples'),
                                           coordinates='C1:C11')

dilution_series4 = protocol.primitive_step('PlateCoordinates',
                                           source=calibration_plate.output_pin('samples'),
                                           coordinates='D1:D11')

dilution_series5 = protocol.primitive_step('PlateCoordinates',
                                           source=calibration_plate.output_pin('samples'),
                                           coordinates='E1:E11')

dilution_series6 = protocol.primitive_step('PlateCoordinates',
                                           source=calibration_plate.output_pin('samples'),
                                           coordinates='F1:F11')

dilution_series7 = protocol.primitive_step('PlateCoordinates',
                                           source=calibration_plate.output_pin('samples'),
                                           coordinates='G1:G11')

dilution_series8 = protocol.primitive_step('PlateCoordinates',
                                           source=calibration_plate.output_pin('samples'),
                                           coordinates='H1:H11')


serial_dilution1 = protocol.primitive_step('SerialDilution',
                                          source=fluorescein_wells_A1.output_pin('samples'),
                                          destination=dilution_series1.output_pin('samples'),
                                          amount=sbol3.Measure(200, OM.microlitre),
                                          diluent=pbs,
                                          dilution_factor=2,
                                          series=10)
serial_dilution1.description = ' For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.'

embedded_image = protocol.primitive_step('EmbeddedImage',
                                         image=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'serial_dilution.png'),
                                         caption="Serial Dilution")

serial_dilution2 = protocol.primitive_step('SerialDilution',
                                          source=fluorescein_wells_B1.output_pin('samples'),
                                          destination=dilution_series2.output_pin('samples'),
                                          amount=sbol3.Measure(200, OM.microlitre),
                                          diluent=pbs,
                                          dilution_factor=2,
                                          series=10)
serial_dilution2.description = ' For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.'

serial_dilution3 = protocol.primitive_step('SerialDilution',
                                          source=sulforhodamine_wells_C1.output_pin('samples'),
                                          destination=dilution_series3.output_pin('samples'),
                                          amount=sbol3.Measure(200, OM.microlitre),
                                          diluent=pbs,
                                          dilution_factor=2,
                                          series=10)
serial_dilution3.description = ' For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.'

serial_dilution4 = protocol.primitive_step('SerialDilution',
                                          source=sulforhodamine_wells_D1.output_pin('samples'),
                                          destination=dilution_series4.output_pin('samples'),
                                          amount=sbol3.Measure(200, OM.microlitre),
                                          diluent=pbs,
                                          dilution_factor=2,
                                          series=10)
serial_dilution4.description = ' For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.'

serial_dilution5 = protocol.primitive_step('SerialDilution',
                                          source=cascade_blue_wells_E1.output_pin('samples'),
                                          destination=dilution_series5.output_pin('samples'),
                                          amount=sbol3.Measure(200, OM.microlitre),
                                          diluent=ddh2o,
                                          dilution_factor=2,
                                          series=10)
serial_dilution5.description = ' For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.'

serial_dilution6 = protocol.primitive_step('SerialDilution',
                                          source=cascade_blue_wells_F1.output_pin('samples'),
                                          destination=dilution_series6.output_pin('samples'),
                                          amount=sbol3.Measure(200, OM.microlitre),
                                          diluent=ddh2o,
                                          dilution_factor=2,
                                          series=10)
serial_dilution6.description = ' For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.'

serial_dilution7 = protocol.primitive_step('SerialDilution',
                                          source=silica_beads_wells_G1.output_pin('samples'),
                                          destination=dilution_series7.output_pin('samples'),
                                          amount=sbol3.Measure(200, OM.microlitre),
                                          diluent=ddh2o,
                                          dilution_factor=2,
                                          series=10)
serial_dilution7.description = ' For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.'

serial_dilution8 = protocol.primitive_step('SerialDilution',
                                          source=silica_beads_wells_H1.output_pin('samples'),
                                          destination=dilution_series8.output_pin('samples'),
                                          amount=sbol3.Measure(200, OM.microlitre),
                                          diluent=ddh2o,
                                          dilution_factor=2,
                                          series=10)
serial_dilution8.description = ' For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.'





discard_wells = protocol.primitive_step('PlateCoordinates',
                                        source=calibration_plate.output_pin('samples'),
                                        coordinates='A11:H11')

discard = protocol.primitive_step('Discard',
                                  samples=discard_wells.output_pin('samples'),
                                  amount=sbol3.Measure(100, OM.microlitre))

discard.description = ' This step ensures that all wells contain an equivalent volume. Be sure to change pipette tips for every well to avoid cross-contamination'

# Bring to volume of 200 ul
samples_in_pbs = protocol.primitive_step('PlateCoordinates',
                                           source=calibration_plate.output_pin('samples'),
                                           coordinates='A1:D12')
samples_in_ddh2o = protocol.primitive_step('PlateCoordinates',
                                           source=calibration_plate.output_pin('samples'),
                                           coordinates='E1:H12')
btv1 = protocol.primitive_step('Transfer',
                               source=pbs,
                               destination=samples_in_pbs.output_pin('samples'),
                               amount=sbol3.Measure(100, OM.microlitre))
btv1.description = ' This will bring all wells to volume 200 microliter.'
btv2 = protocol.primitive_step('Transfer',
                               source=ddh2o,
                               destination=samples_in_ddh2o.output_pin('samples'),
                               amount=sbol3.Measure(100, OM.microlitre))
btv2.description = ' This will bring all wells to volume 200 microliter.'




# Perform measurements
read_wells1 = protocol.primitive_step('PlateCoordinates',
                                      source=calibration_plate.output_pin('samples'),
                                      coordinates='A1:B12')
read_wells2 = protocol.primitive_step('PlateCoordinates',
                                      source=calibration_plate.output_pin('samples'),
                                      coordinates='C1:D12')
read_wells3 = protocol.primitive_step('PlateCoordinates',
                                      source=calibration_plate.output_pin('samples'),
                                      coordinates='E1:F12')
read_wells4 = protocol.primitive_step('PlateCoordinates',
                                      source=calibration_plate.output_pin('samples'),
                                      coordinates='G1:H12')

measure_fluorescence1 = protocol.primitive_step('MeasureFluorescence',
                                               samples=read_wells1.output_pin('samples'),
                                               excitationWavelength=sbol3.Measure(488, OM.nanometer),
                                               emissionWavelength=sbol3.Measure(530, OM.nanometer),
                                               emissionBandpassWidth=sbol3.Measure(30, OM.nanometer))
measure_fluorescence1.name = 'fluorescein and bead fluorescence'

measure_fluorescence2 = protocol.primitive_step('MeasureFluorescence',
                                               samples=read_wells2.output_pin('samples'),
                                               excitationWavelength=sbol3.Measure(561, OM.nanometer),
                                               emissionWavelength=sbol3.Measure(610, OM.nanometer),
                                               emissionBandpassWidth=sbol3.Measure(20, OM.nanometer))
measure_fluorescence2.name = 'sulforhodamine 101 fluorescence'

measure_fluorescence3 = protocol.primitive_step('MeasureFluorescence',
                                               samples=read_wells3.output_pin('samples'),
                                               excitationWavelength=sbol3.Measure(405, OM.nanometer),
                                               emissionWavelength=sbol3.Measure(450, OM.nanometer),
                                               emissionBandpassWidth=sbol3.Measure(50, OM.nanometer))
measure_fluorescence3.name = 'cascade blue fluorescence'

measure_absorbance = protocol.primitive_step('MeasureAbsorbance',
                                             samples=read_wells4.output_pin('samples'),
                                             wavelength=sbol3.Measure(600, OM.nanometer))

load_excel = protocol.primitive_step('ExcelMetadata',
                                     for_samples=calibration_plate.output_pin('samples'),
                                     filename=os.path.join(os.path.dirname(
                                                  os.path.realpath(__file__)),
                                                  'metadata/sample_metadata.xlsx'))

meta1 = protocol.primitive_step("JoinMetadata",
                              dataset=measure_fluorescence1.output_pin('measurements'),
                              metadata=load_excel.output_pin('metadata'))

meta2 = protocol.primitive_step("JoinMetadata",
                              dataset=measure_fluorescence2.output_pin('measurements'),
                              metadata=load_excel.output_pin('metadata'))

meta3 = protocol.primitive_step("JoinMetadata",
                              dataset=measure_fluorescence3.output_pin('measurements'),
                              metadata=load_excel.output_pin('metadata'))

meta4 = protocol.primitive_step("JoinMetadata",
                              dataset=measure_absorbance.output_pin('measurements'),
                              metadata=load_excel.output_pin('metadata'))

final_dataset = protocol.primitive_step("JoinDatasets",
                              dataset=[meta1.output_pin('enhanced_dataset'),
                                       meta2.output_pin('enhanced_dataset'),
                                       meta3.output_pin('enhanced_dataset'),
                                       meta4.output_pin('enhanced_dataset')]
                              )
protocol.designate_output('dataset', 'http://bioprotocols.org/labop#Dataset', source=final_dataset.output_pin('joint_dataset'))

ee = ExecutionEngine(specializations=[
        # MarkdownSpecialization(__file__.split('.')[0] + '.md')
    ],
    failsafe=False, sample_format='xarray')
execution = ee.execute(protocol, sbol3.Agent('test_agent'), id="test_execution", parameter_values=[])

dataset = ee.ex.parameter_values[0].value.get_value().to_dataset()
with open(__file__.split('.')[0] + '.csv', 'w', encoding='utf-8') as f:
    f.write(dataset.to_dataframe().to_csv())

print(execution.markdown)

# Dress up the markdown to make it pretty and more readable
execution.markdown = execution.markdown.replace(' milliliter', 'mL')
execution.markdown = execution.markdown.replace(' nanometer', 'nm')
execution.markdown = execution.markdown.replace(' microliter', 'uL')

with open(__file__.split('.')[0] + '.md', 'w', encoding='utf-8') as f:
    f.write(execution.markdown)
