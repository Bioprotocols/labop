# Testing the three color calibration protocol

In this experiment, your team will measure the fluorescence of six devices that encode either a single fluorescence protein (blue, green, or red) or two fluorescence proteins encoded in two transcriptional units. You will calibrate the fluorescence of these devices to the three calibrant dyes and you will calibrate the optical density of the culture to the cell density calibrant.

This experiment aims to assess the lab-to-lab reproducibility of the new three color calibration protocol. We will test if it works well for calibrating the fluorescence in cells that express one single fluorescent protein and for cells expressing two different fluorescent proteins at the same time.

Before performing the cell measurements, you need to perform all the calibration measurements. Please do not proceed unless you have completed the calibration protocol. Completion of the calibrations will ensure that you understand the measurement process and that you can take the cell measurements under the same conditions. For consistency and reproducibility, we are requiring all teams to use E. coli K-12 DH5-alpha. If you do not have access to this strain, you can request streaks of the transformed devices from another team near you. If you are absolutely unable to obtain the DH5-alpha strain, you may still participate in the InterLab study by contacting the Engineering Committee (engineering [at] igem [dot] org) to discuss your situation.

For all below indicated cell measurements, you must use the same type of plates and the same volumes that you used in your calibration protocol. You must also use the same settings (e.g., filters or excitation and emission wavelengths) that you used in your calibration measurements. If you do not use the same type of plates, volumes, and settings, the measurements will not be valid.

Protocol summary: You will transform the eight devices listed in Table 1 into E. coli K-12 DH5-alpha cells. The next day you will pick two colonies from each transformation (16 total) and use them to inoculate 5 mL overnight cultures (this step is still in tubes). Each of these 16 overnight cultures will be used to inoculate four wells in a 96-well plate (200uL each, 4 replicates) and one test tube (12 mL). You will measure how fluorescence and optical density develops over 6 hours by taking measurements at time point 0 hour and at time point 6 hours. Follow the protocol below and the visual instructions in Figure 1 and Figure 2.


## Protocol Outputs:
* Dataset: [test_LUDOX_markdown.xlsx](test_LUDOX_markdown.xlsx)
* Dataset: [test_LUDOX_markdown.xlsx](test_LUDOX_markdown.xlsx)
* Dataset: [test_LUDOX_markdown.xlsx](test_LUDOX_markdown.xlsx)
* Dataset: [test_LUDOX_markdown.xlsx](test_LUDOX_markdown.xlsx)
* Dataset: [test_LUDOX_markdown.xlsx](test_LUDOX_markdown.xlsx)
* Dataset: [test_LUDOX_markdown.xlsx](test_LUDOX_markdown.xlsx)
* Dataset: [test_LUDOX_markdown.xlsx](test_LUDOX_markdown.xlsx)
* Dataset: [test_LUDOX_markdown.xlsx](test_LUDOX_markdown.xlsx)
* Dataset: [test_LUDOX_markdown.xlsx](test_LUDOX_markdown.xlsx)


## Protocol Materials:
* [_E. coli_ DH5 alpha competent cells](https://identifiers.org/taxonomy:668369)
* [Negative control 2022](http://parts.igem.org/Part:BBa_J428100)
* [Positive control 2018](http://parts.igem.org/Part:BBa_I20270)
* [Test Device 1 Exp 1 (Green Device)](http://parts.igem.org/Part:BBa_J428112)
* [Test Device 2 Exp 1 (Red mRFP1 device)](http://parts.igem.org/Part:BBa_J428110)
* [Test Device 3 Exp 1 (Red mCherry device)](http://parts.igem.org/Part:BBa_J428111)
* [Test Device 4 Exp 1 (RiboJ Insulated mCherry device)](http://parts.igem.org/Part:BBa_J428101)
* [Test Device 5 Exp 1 (Dual construct Blue and Red)](http://parts.igem.org/Part:BBa_J428108)
* [Test Device 6 Exp 1 (Dual construct Green and Blue)](http://parts.igem.org/Part:BBa_J428106)
* [LB Broth + Chloramphenicol (34 ug/mL)]()
* [LB Agar + Chloramphenicol (34 ug/mL)]()
* [Chloramphenicol stock solution (34 mg/mL)](https://pubchem.ncbi.nlm.nih.gov/compound/5959)
* [Ice]()
* [Plate reader]()
* [Shaking incubator]()
* Petri dish (x 8)
* culture tube (x 32)
* 1.5 mL microfuge tube (x 32)
* 50 ml conical tube (x 16)
* 96 well plate (x 2)


#### Table 1: Part Locations in Distribution Kit
| Part | Coordinate |
| ---- | -------------- |
|BBa_J428100|Kit Plate 1 Well 12M|
|BBa_I20270|Kit Plate 1 Well 1A|
|BBa_J428112|Kit Plate 1 Well 14C|
|BBa_J428110|Kit Plate 1 Well 12O|
|BBa_J428111|Kit Plate 1 Well 14A|
|BBa_J428101|Kit Plate 1 Well 12I|
|BBa_J428108|Kit Plate 1 Well 14E|
|BBa_J428106|Kit Plate 1 Well 12G|


## Protocol Steps:
1. Obtain 8 x Petri dish containing LB Agar + Chloramphenicol (34 ug/mL) growth medium for culturing `transformant strains`
2. Transform `Negative control 2022` DNA into _`E. coli`_ ` DH5 alpha competent cells`. Repeat for the remaining transformant DNA:  `Positive control 2018`, `Test Device 1 Exp 1 (Green Device)`, `Test Device 2 Exp 1 (Red mRFP1 device)`, `Test Device 3 Exp 1 (Red mCherry device)`, `Test Device 4 Exp 1 (RiboJ Insulated mCherry device)`, `Test Device 5 Exp 1 (Dual construct Blue and Red)`, and `Test Device 6 Exp 1 (Dual construct Green and Blue)`. Plate transformants on LB Agar + Chloramphenicol (34 ug/mL) `transformant strains` plates. Incubate overnight (for 16 hour) at 37.0°C.
3. Obtain 16 x culture tubes to contain `culture (day 1)`
4. Pick 2 colonies from each `transformant strains` plate.
5. Inoculate 2 colonies of each transformant strains, for a total of 16 cultures. Inoculate each into 5.0mL of LB Broth + Chloramphenicol (34 ug/mL) in culture (day 1) and grow overnight (for 16.0 hour) at 37.0°C and 220 rpm.
6. Obtain 16 x culture tubes to contain `culture (day 2)`
7. Dilute each of 16 `culture (day 1)` samples with LB Broth + Chloramphenicol (34 ug/mL) into the culture tube at a 1:10 ratio and final volume of 5.0mL. Maintain at 4.0°C while performing dilutions. (This can be also performed on ice).
8. Obtain 16 x 1.5 mL microfuge tubes to contain `cultures (0 hr timepoint)`
9. Hold `cultures (0 hr timepoint)` on ice. This will prevent cell growth while transferring samples.
10. Transfer 1.0mL of each of 16 `culture (day 2)` samples to wells <xarray.Dataset>
Dimensions:  ()
Data variables:
    *empty* of 1.5 mL microfuge tube containers to contain a total of 16 `cultures (0 hr timepoint)` samples. Maintain at 4.0°C during transfer. (This can be also performed on Ice).
11. Measure baseline absorbance of culture (day 2) of `cultures (0 hr timepoint)` at 600.0nm.
12. Obtain 16 x 50 ml conical tubes to contain `back-diluted culture` The conical tube should be opaque, amber-colored, or covered with foil.
13. Back-dilute each of 16 `culture (day 2)` samples to a target OD of 0.02 using LB Broth + Chloramphenicol (34 ug/mL) as diluent to a final volume of 12.0mL. Maintain at 4.0°C while performing dilutions.

![](Exp1_2_protocol_published.png)
<p align="center">Fig 1: Visual representation of protocol</p>

14. Obtain 16 x 1.5 mL microfuge tubes to contain `back-diluted culture aliquots`
15. Hold `back-diluted culture aliquots` on ice. This will prevent cell growth while transferring samples.
16. Transfer 1.0mL of each of 16 `back-diluted culture` samples to wells <xarray.Dataset>
Dimensions:  ()
Data variables:
    *empty* of 1.5 mL microfuge tube containers to contain a total of 16 `back-diluted culture aliquots` samples. Maintain at 4.0°C during transfer. (This can be also performed on Ice).
17. Provision a container named `plate 1` such as: 
	[NEST96WellPlate](https://sift.net/container-ontology/container-ontology#NEST96WellPlate),
	[Corning96WellPlate360uLFlat](https://sift.net/container-ontology/container-ontology#Corning96WellPlate360uLFlat).
18. Hold all `None` samples on ice.
19. Transfer 200.0uL of each `back-diluted culture aliquots` sample to 96 well plate `plate 1` in the wells indicated in the plate layout.
 Maintain at 4.0°C during transfer.
20. Transfer 200.0uL of `LB Broth + Chloramphenicol (34 ug/mL)` sample to wells {'A1': None, 'B1': None, 'C1': None, 'D1': None, 'E1': None, 'F1': None, 'G1': None, 'H1': None, 'A2': None, 'B2': None, 'C2': None, 'D2': None, 'E2': None, 'F2': None, 'G2': None, 'H2': None, 'A3': None, 'B3': None, 'C3': None, 'D3': None, 'E3': None, 'F3': None, 'G3': None, 'H3': None, 'A4': None, 'B4': None, 'C4': None, 'D4': None, 'E4': None, 'F4': None, 'G4': None, 'H4': None, 'A5': None, 'B5': None, 'C5': None, 'D5': None, 'E5': None, 'F5': None, 'G5': None, 'H5': None, 'A6': None, 'B6': None, 'C6': None, 'D6': None, 'E6': None, 'F6': None, 'G6': None, 'H6': None, 'A7': None, 'B7': None, 'C7': None, 'D7': None, 'E7': None, 'F7': None, 'G7': None, 'H7': None, 'A8': None, 'B8': None, 'C8': None, 'D8': None, 'E8': None, 'F8': None, 'G8': None, 'H8': None, 'A9': None, 'B9': None, 'C9': None, 'D9': None, 'E9': None, 'F9': None, 'G9': None, 'H9': None, 'A10': None, 'B10': None, 'C10': None, 'D10': None, 'E10': None, 'F10': None, 'G10': None, 'H10': None, 'A11': None, 'B11': None, 'C11': None, 'D11': None, 'E11': None, 'F11': None, 'G11': None, 'H11': None, 'A12': None, 'B12': None, 'C12': None, 'D12': None, 'E12': None, 'F12': None, 'G12': None, 'H12': None} of  96 well plate `plate 1`. Maintain at 4.0°C during transfer. These samples are blanks.

![](fig2_cell_calibration.png)
<p align="center">Fig 2: Plate layout</p>

21. Measure 0 hr absorbance timepoint of `plate 1` at 600.0nm.
22. Measure 0 hr green fluorescence timepoint of `plate 1` with excitation wavelength of 488.0nm and emission filter of 530.0nm and 30.0nm bandpass.
23. Measure 0 hr blue fluorescence timepoint of `plate 1` with excitation wavelength of 405.0nm and emission filter of 450.0nm and 50.0nm bandpass.
24. Measure 0 hr red fluorescence timepoint of `plate 1` with excitation wavelength of 561.0nm and emission filter of 610.0nm and 20.0nm bandpass.
25. Incubate all `back-diluted culture` samples for 6.0 hour at 37.0°C at 220 rpm.
26. Hold all `back-diluted culture` samples on ice. This will inhibit cell growth during the subsequent pipetting steps.
27. Provision a container named `plate 2` such as: 
	[NEST96WellPlate](https://sift.net/container-ontology/container-ontology#NEST96WellPlate),
	[Corning96WellPlate360uLFlat](https://sift.net/container-ontology/container-ontology#Corning96WellPlate360uLFlat).
28. Hold all `None` samples on ice.
29. Transfer 200.0uL of each `back-diluted culture` sample to 96 well plate `plate 2` in the wells indicated in the plate layout.
 Maintain at 4.0°C during transfer.
30. Transfer 200.0uL of `LB Broth + Chloramphenicol (34 ug/mL)` sample to wells {'A1': None, 'B1': None, 'C1': None, 'D1': None, 'E1': None, 'F1': None, 'G1': None, 'H1': None, 'A2': None, 'B2': None, 'C2': None, 'D2': None, 'E2': None, 'F2': None, 'G2': None, 'H2': None, 'A3': None, 'B3': None, 'C3': None, 'D3': None, 'E3': None, 'F3': None, 'G3': None, 'H3': None, 'A4': None, 'B4': None, 'C4': None, 'D4': None, 'E4': None, 'F4': None, 'G4': None, 'H4': None, 'A5': None, 'B5': None, 'C5': None, 'D5': None, 'E5': None, 'F5': None, 'G5': None, 'H5': None, 'A6': None, 'B6': None, 'C6': None, 'D6': None, 'E6': None, 'F6': None, 'G6': None, 'H6': None, 'A7': None, 'B7': None, 'C7': None, 'D7': None, 'E7': None, 'F7': None, 'G7': None, 'H7': None, 'A8': None, 'B8': None, 'C8': None, 'D8': None, 'E8': None, 'F8': None, 'G8': None, 'H8': None, 'A9': None, 'B9': None, 'C9': None, 'D9': None, 'E9': None, 'F9': None, 'G9': None, 'H9': None, 'A10': None, 'B10': None, 'C10': None, 'D10': None, 'E10': None, 'F10': None, 'G10': None, 'H10': None, 'A11': None, 'B11': None, 'C11': None, 'D11': None, 'E11': None, 'F11': None, 'G11': None, 'H11': None, 'A12': None, 'B12': None, 'C12': None, 'D12': None, 'E12': None, 'F12': None, 'G12': None, 'H12': None, 'A2:D2': 'http://igem.org/engineering/transformant1', 'E2:H2': 'http://igem.org/engineering/transformant2', 'A3:D3': 'http://igem.org/engineering/transformant3', 'E3:H3': 'http://igem.org/engineering/transformant4', 'A4:D4': 'http://igem.org/engineering/transformant5', 'E4:H4': 'http://igem.org/engineering/transformant6', 'A5:D5': 'http://igem.org/engineering/transformant7', 'E5:H5': 'http://igem.org/engineering/transformant8', 'A7:D7': 'http://igem.org/engineering/transformant1', 'E7:H7': 'http://igem.org/engineering/transformant2', 'A8:D8': 'http://igem.org/engineering/transformant3', 'E8:H8': 'http://igem.org/engineering/transformant4', 'A9:D9': 'http://igem.org/engineering/transformant5', 'E9:H9': 'http://igem.org/engineering/transformant6', 'A10:D10': 'http://igem.org/engineering/transformant7', 'E10:H10': 'http://igem.org/engineering/transformant8'} of  96 well plate `plate 2`. Maintain at 4.0°C during transfer. These are the blanks.
31. Measure 6 hr absorbance timepoint of `plate 2` at 600.0nm.
32. Measure 6 hr green fluorescence timepoint of `plate 2` with excitation wavelength of 485.0nm and emission filter of 530.0nm and 30.0nm bandpass.
33. Measure 6 hr blue fluorescence timepoint of `plate 2` with excitation wavelength of 405.0nm and emission filter of 450.0nm and 50.0nm bandpass.
34. Measure 6 hr red fluorescence timepoint of `plate 2` with excitation wavelength of 561.0nm and emission filter of 610.0nm and 20.0nm bandpass.
35. Import data into the provided Excel file: `baseline absorbance of culture (day 2) measurements of cultures (0 hr timepoint)`, `0 hr absorbance timepoint measurements of plate 1`, `0 hr green fluorescence timepoint measurements of plate 1`, `0 hr blue fluorescence timepoint measurements of plate 1`, `0 hr red fluorescence timepoint measurements of plate 1`, `6 hr absorbance timepoint measurements of plate 2`, `6 hr green fluorescence timepoint measurements of plate 2`, `6 hr blue fluorescence timepoint measurements of plate 2`, `6 hr red fluorescence timepoint measurements of plate 2`.
---
Timestamp: 2023-03-11 16:05:32.866480
Protocol version: 1.1b
