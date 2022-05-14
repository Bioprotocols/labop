# Cell measurement protocol

## Description:
Challenging B - This version of the interlab protocol involves 2 hr. time interval measurements and incubation inside a microplate reader/incubator.

Prior to performing the cell measurements you should perform all three of the calibration measurements. Please do not proceed unless you have completed the three calibration protocols. Completion of the calibrations will ensure that you understand the measurement process and that you can take the cell measurements under the same conditions. For the sake of consistency and reproducibility, we are requiring all teams to use E. coli K-12 DH5-alpha. If you do not have access to this strain, you can request streaks of the transformed devices from another team near you, and this can count as a collaboration as long as it is appropriately documented on both teams' wikis. If you are absolutely unable to obtain the DH5-alpha strain, you may still participate in the InterLab study by contacting the Measurement Committee (measurement at igem dot org) to discuss your situation.

For all of these cell measurements, you must use the same plates and volumes that you used in your calibration protocol. You must also use the same settings (e.g., filters or excitation and emission wavelengths) that you used in your calibration measurements. If you do not use the same plates, volumes, and settings, the measurements will not be valid.


## Protocol Materials:
* [_E. coli_ DH5 alpha](https://identifiers.org/pubchem.substance:24901740)
* [LB Broth+chloramphenicol](https://identifiers.org/pubchem.substance:24901740)
* [chloramphenicol](https://identifiers.org/pubchem.substance:24901740)
* [Negative control](https://identifiers.org/SBO:0000251)
* [Positive control](https://identifiers.org/SBO:0000251)
* [Test Device 1](https://identifiers.org/SBO:0000251)
* [Test Device 2](https://identifiers.org/SBO:0000251)
* [Test Device 3](https://identifiers.org/SBO:0000251)
* [Test Device 4](https://identifiers.org/SBO:0000251)
* [Test Device 5](https://identifiers.org/SBO:0000251)
* [Test Device 6](https://identifiers.org/SBO:0000251)


## Protocol Inputs:


## Protocol Outputs:
* `baseline absorbance of culture (day 2) measurements of cultures (0 hr timepoint)`
* `0 hr absorbance timepoint measurements of plate 1`
* `0 hr fluorescence timepoint measurements of plate 1`
* `absorbance timepoint measurements of plate 1 at timepoints 2.0 hour, 4.0 hour, 6.0 hour`
* `fluorescence timepoint measurements of plate 1 at timepoints 2.0 hour, 4.0 hour, 6.0 hour`
* `absorbance timepoint measurements of Plates 2, 3, and 4`
* `fluorescence timepoint measurements of Plates 2, 3, and 4`


## Steps
1. Transform `Negative control` DNA into _`E. coli`_ ` DH5 alpha` and plate transformants on LB Broth+chloramphenicol. Repeat for the remaining transformant DNA:  `Positive control`, `Test Device 1`, `Test Device 2`, `Test Device 3`, `Test Device 4`, `Test Device 5`, and `Test Device 6`.
2. Provision 16 x culture tubes to contain `culture (day 1)`
3. Inoculate _`E. coli`_ ` DH5 alpha+Negative control transformant` into 5.0 milliliter of LB Broth+chloramphenicol in culture (day 1) and grow for 16.0 hour at 37.0 degree Celsius and 220.0 rpm.  Repeat this procedure for the other inocula:  _`E. coli`_ ` DH5 alpha+Positive control transformant`, _`E. coli`_ ` DH5 alpha+Test Device 1 transformant`, _`E. coli`_ ` DH5 alpha+Test Device 2 transformant`, _`E. coli`_ ` DH5 alpha+Test Device 3 transformant`, _`E. coli`_ ` DH5 alpha+Test Device 4 transformant`, _`E. coli`_ ` DH5 alpha+Test Device 5 transformant`, and _`E. coli`_ ` DH5 alpha+Test Device 6 transformant`. Inoculate 2 replicates for each transformant, for a total of 16 cultures.
4. Provision 16 x culture tubes to contain `culture (day 2)`
5. Dilute each of 16 `culture (day 1)` samples with LB Broth+chloramphenicol into the culture tube at a 1:10 ratio and final volume of 10.0 milliliter. Maintain at 4.0 degree Celsius while performing dilutions.
6. Provision 16 x 1.5 mL microfuge tubes to contain `cultures (0 hr timepoint)`
7. Hold `cultures (0 hr timepoint)` at 4.0 degree Celsius. This will prevent cell growth while transferring samples.
8. Transfer 1.0 milliliter of each of 16 `culture (day 2)` samples to 1.5 mL microfuge tube containers to contain a total of 16 `cultures (0 hr timepoint)` samples. Maintain at 4.0 degree Celsius during transfer.
9. Measure baseline absorbance of culture (day 2) of `cultures (0 hr timepoint)` at 600.0 nanometer.
10. Provision 16 x 50 ml conical tubes to contain `back-diluted culture` The conical tube should be opaque, amber-colored, or covered with foil.
11. Back-dilute each of 16 `culture (day 2)` samples to a target OD of 0.02 using LB Broth+chloramphenicol as diluent to a final volume of 40.0 milliliter. Maintain at 4.0 degree Celsius while performing dilutions.

![](/Users/bbartley/Dev/git/sd2/paml/fig1_cell_calibration.png)


12. Provision 16 x 50 ml conical tubes to contain `Tubes 1, 2 and 3` The conical tubes should be opaque, amber-colored, or covered with foil.
13. Provision 16 x 50 ml conical tubes to contain `Tube 2` The conical tubes should be opaque, amber-colored, or covered with foil.
14. Provision 16 x 50 ml conical tubes to contain `Tube 3` The conical tubes should be opaque, amber-colored, or covered with foil.
15. Transfer 1.0 milliliter of each of 16 `back-diluted culture` samples to 50 ml conical tube containers to contain a total of 16 `Tubes 1, 2 and 3` samples. Maintain at 4.0 degree Celsius during transfer.
16. Transfer 1.0 milliliter of each of 16 `back-diluted culture` samples to 50 ml conical tube containers to contain a total of 16 `Tube 2` samples. Maintain at 4.0 degree Celsius during transfer.
17. Transfer 1.0 milliliter of each of 16 `back-diluted culture` samples to 50 ml conical tube containers to contain a total of 16 `Tube 3` samples. Maintain at 4.0 degree Celsius during transfer.
18. Provision a 96 well microplate to contain `plate 1`
19. Hold `plate 1` at 4.0 degree Celsius.
20. Transfer 100.0 microliter of each `Tubes 1, 2 and 3` sample to 96 well microplate `plate 1` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
21. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate 1`. Maintain at 4.0 degree Celsius during transfer. These samples are blanks.

![](/Users/bbartley/Dev/git/sd2/paml/fig2_cell_calibration.png)


22. Cover `plate 1` samples in 96 well microplate with your choice of material to prevent evaporation.
23. Measure 0 hr absorbance timepoint of `plate 1` at 600.0 nanometer.
24. Measure 0 hr fluorescence timepoint of `plate 1` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
25. Incubate all `plate 1` samples for 6.0 hour at 37.0 degree Celsius at 220.0 rpm.
26. Measure absorbance timepoint of `plate 1` at 600.0 nanometer at timepoints 2.0 hour, 4.0 hour, 6.0 hour.
27. Measure fluorescence timepoint of `plate 1` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass at timepoints 2.0 hour, 4.0 hour, 6.0 hour.
28. Incubate all `Tubes 1, 2 and 3` samples for 2.0 hour at 37.0 degree Celsius at 220.0 rpm.
29. Hold all `Tubes 1, 2 and 3` samples at 4.0 degree Celsius. Reserve until the end of the experiment for absorbance and fluorescence measurements.
30. Incubate all `Tube 2` samples for 4.0 hour at 37.0 degree Celsius at 220.0 rpm.
31. Hold all `Tube 2` samples at 4.0 degree Celsius. Reserve until the end of the experiment for absorbance and fluorescence measurements.
32. Incubate all `Tube 3` samples for 6.0 hour at 37.0 degree Celsius at 220.0 rpm.
33. Hold all `Tube 3` samples at 4.0 degree Celsius. Reserve until the end of the experiment for absorbance and fluorescence measurements.
34. Provision a 96 well microplate to contain `Plates 2, 3, and 4`
35. Transfer 100.0 microliter of each `Tubes 1, 2 and 3` sample to 96 well microplate `Plates 2, 3, and 4` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
36. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `Plates 2, 3, and 4`. Maintain at 4.0 degree Celsius during transfer. These samples are blanks.
37. Measure absorbance timepoint of `Plates 2, 3, and 4` at 600.0 nanometer.
38. Measure fluorescence timepoint of `Plates 2, 3, and 4` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
39. Import data for `baseline absorbance of culture (day 2) measurements of cultures (0 hr timepoint)`, `0 hr absorbance timepoint measurements of plate 1`, `0 hr fluorescence timepoint measurements of plate 1`, `absorbance timepoint measurements of plate 1 at timepoints 2.0 hour, 4.0 hour, 6.0 hour`, `fluorescence timepoint measurements of plate 1 at timepoints 2.0 hour, 4.0 hour, 6.0 hour`, `absorbance timepoint measurements of Plates 2, 3, and 4`, `fluorescence timepoint measurements of Plates 2, 3, and 4` into provided Excel file.
---
Timestamp: 2022-05-09 06:21:06.952062---
Protocol version: 1.0b