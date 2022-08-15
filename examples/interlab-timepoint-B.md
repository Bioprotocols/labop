# Cell measurement protocol

Challenging B - This version of the interlab protocol involves 2 hr. time interval measurements and incubation inside a microplate reader/incubator.

Prior to performing the cell measurements you should perform all three of the calibration measurements. Please do not proceed unless you have completed the three calibration protocols. Completion of the calibrations will ensure that you understand the measurement process and that you can take the cell measurements under the same conditions. For the sake of consistency and reproducibility, we are requiring all teams to use E. coli K-12 DH5-alpha. If you do not have access to this strain, you can request streaks of the transformed devices from another team near you, and this can count as a collaboration as long as it is appropriately documented on both teams' wikis. If you are absolutely unable to obtain the DH5-alpha strain, you may still participate in the InterLab study by contacting the Measurement Committee (measurement at igem dot org) to discuss your situation.

For all of these cell measurements, you must use the same plates and volumes that you used in your calibration protocol. You must also use the same settings (e.g., filters or excitation and emission wavelengths) that you used in your calibration measurements. If you do not use the same plates, volumes, and settings, the measurements will not be valid.


## Protocol Outputs:
* `baseline absorbance of culture (day 2) measurements of cultures (0 hr timepoint)`
* `0 hr absorbance timepoint measurements of plate 1`
* `0 hr fluorescence timepoint measurements of plate 1`
* `absorbance timepoint measurements of plate 1 at timepoints 2.0 hour, 4.0 hour, 6.0 hour`
* `fluorescence timepoint measurements of plate 1 at timepoints 2.0 hour, 4.0 hour, 6.0 hour`
* `absorbance timepoint measurements of Plates 2, 3, and 4`
* `fluorescence timepoint measurements of Plates 2, 3, and 4`


## Protocol Materials:
* [_E. coli_ DH5 alpha](https://identifiers.org/taxonomy:668369)
* [LB Broth+chloramphenicol]()
* [LB Agar + Chloramphenicol]()
* [chloramphenicol](https://pubchem.ncbi.nlm.nih.gov/compound/5959)
* [Negative control (J428100)](http://parts.igem.org/Part:BBa_J428100)
* [Positive control (I20270)](http://parts.igem.org/Part:BBa_I20270)
* [Test Device 1 (J364000)](http://parts.igem.org/Part:BBa_J364000)
* [Test Device 2 (J364001)](http://parts.igem.org/Part:BBa_J364001)
* [Test Device 3 (J364002)](http://parts.igem.org/Part:BBa_J364002)
* [Test Device 4 (J364007)](http://parts.igem.org/Part:BBa_J364007)
* [Test Device 5 (J364008)](http://parts.igem.org/Part:BBa_J364008)
* [Test Device 6 (J364009)](http://parts.igem.org/Part:BBa_J364009)


#### Part Locations in Distribution Kit
| Part | Coordinate |
| ---- | -------------- |
|BBa_J428100|Kit Plate 1 Well 12M|
|BBa_I20270|Kit Plate 1 Well 1A|
|BBa_J364000|Kit Plate 1 Well 1C|
|BBa_J364001|Kit Plate 1 Well 1E|
|BBa_J364002|Kit Plate 1 Well 1G|
|BBa_J364007|Kit Plate 1 Well 1I|
|BBa_J364008|Kit Plate 1 Well 1K|
|BBa_J364009|Kit Plate 1 Well 1M|


## Protocol Steps:
1. Provision 8 x culture plate containing LB Agar + Chloramphenicol growth medium for culturing `test strains`
2. Transform `Negative control (J428100)` DNA into _`E. coli`_ ` DH5 alpha` and plate transformants on LB Broth+chloramphenicol. Repeat for the remaining transformant DNA:  `Positive control (I20270)`, `Test Device 1 (J364000)`, `Test Device 2 (J364001)`, `Test Device 3 (J364002)`, `Test Device 4 (J364007)`, `Test Device 5 (J364008)`, and `Test Device 6 (J364009)`. Plate transformants on `test strains` plates.
3. Provision 16 x culture tubes to contain `culture (day 1)`
4. Pick 2 colonies from each `test strains` plate.
5. Inoculate 2 colonies of each transformant test strains, for a total of 16 cultures. Inoculate each into 5.0 milliliter of LB Broth+chloramphenicol in culture (day 1) and grow for 16.0 hour at 37.0 degree Celsius and 220.0 rpm.
6. Provision 16 x culture tubes to contain `culture (day 2)`
7. Dilute each of 16 `culture (day 1)` samples with LB Broth+chloramphenicol into the culture tube at a 1:10 ratio and final volume of 10.0 milliliter. Maintain at 4.0 degree Celsius while performing dilutions.
8. Provision 16 x 1.5 mL microfuge tubes to contain `cultures (0 hr timepoint)`
9. Hold `cultures (0 hr timepoint)` at 4.0 degree Celsius. This will prevent cell growth while transferring samples.
10. Transfer 1.0 milliliter of each of 16 `culture (day 2)` samples to 1.5 mL microfuge tube containers to contain a total of 16 `cultures (0 hr timepoint)` samples. Maintain at 4.0 degree Celsius during transfer.
11. Measure baseline absorbance of culture (day 2) of `cultures (0 hr timepoint)` at 600.0 nanometer.
12. Provision 16 x 50 ml conical tubes to contain `back-diluted culture` The conical tube should be opaque, amber-colored, or covered with foil.
13. Back-dilute each of 16 `culture (day 2)` samples to a target OD of 0.02 using LB Broth+chloramphenicol as diluent to a final volume of 40.0 milliliter. Maintain at 4.0 degree Celsius while performing dilutions.

![](/Users/bbartley/Dev/git/sd2/paml/examples/fig1_cell_calibration.png)


14. Provision 16 x 50 ml conical tubes to contain `Tubes 1, 2 and 3` The conical tubes should be opaque, amber-colored, or covered with foil.
15. Provision 16 x 50 ml conical tubes to contain `Tube 2` The conical tubes should be opaque, amber-colored, or covered with foil.
16. Provision 16 x 50 ml conical tubes to contain `Tube 3` The conical tubes should be opaque, amber-colored, or covered with foil.
17. Transfer 1.0 milliliter of each of 16 `back-diluted culture` samples to 50 ml conical tube containers to contain a total of 16 `Tubes 1, 2 and 3` samples. Maintain at 4.0 degree Celsius during transfer.
18. Transfer 1.0 milliliter of each of 16 `back-diluted culture` samples to 50 ml conical tube containers to contain a total of 16 `Tube 2` samples. Maintain at 4.0 degree Celsius during transfer.
19. Transfer 1.0 milliliter of each of 16 `back-diluted culture` samples to 50 ml conical tube containers to contain a total of 16 `Tube 3` samples. Maintain at 4.0 degree Celsius during transfer.
20. Provision a 96 well microplate to contain `plate 1`
21. Hold `plate 1` at 4.0 degree Celsius.
22. Transfer 100.0 microliter of each `Tubes 1, 2 and 3` sample to 96 well microplate `plate 1` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
23. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate 1`. Maintain at 4.0 degree Celsius during transfer. These samples are blanks.

![](/Users/bbartley/Dev/git/sd2/paml/fig2_cell_calibration.png)


24. Cover `plate 1` samples in 96 well microplate with your choice of material to prevent evaporation.
25. Measure 0 hr absorbance timepoint of `plate 1` at 600.0 nanometer.
26. Measure 0 hr fluorescence timepoint of `plate 1` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
27. Incubate all `plate 1` samples for 6.0 hour at 37.0 degree Celsius at 220.0 rpm.
28. Measure absorbance timepoint of `plate 1` at 600.0 nanometer at timepoints 2.0 hour, 4.0 hour, 6.0 hour.
29. Measure fluorescence timepoint of `plate 1` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass at timepoints 2.0 hour, 4.0 hour, 6.0 hour.
30. Incubate all `Tubes 1, 2 and 3` samples for 2.0 hour at 37.0 degree Celsius at 220.0 rpm.
31. Hold all `Tubes 1, 2 and 3` samples at 4.0 degree Celsius. Reserve until the end of the experiment for absorbance and fluorescence measurements.
32. Incubate all `Tube 2` samples for 4.0 hour at 37.0 degree Celsius at 220.0 rpm.
33. Hold all `Tube 2` samples at 4.0 degree Celsius. Reserve until the end of the experiment for absorbance and fluorescence measurements.
34. Incubate all `Tube 3` samples for 6.0 hour at 37.0 degree Celsius at 220.0 rpm.
35. Hold all `Tube 3` samples at 4.0 degree Celsius. Reserve until the end of the experiment for absorbance and fluorescence measurements.
36. Provision a 96 well microplate to contain `Plates 2, 3, and 4`
37. Transfer 100.0 microliter of each `Tubes 1, 2 and 3` sample to 96 well microplate `Plates 2, 3, and 4` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
38. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `Plates 2, 3, and 4`. Maintain at 4.0 degree Celsius during transfer. These samples are blanks.
39. Measure absorbance timepoint of `Plates 2, 3, and 4` at 600.0 nanometer.
40. Measure fluorescence timepoint of `Plates 2, 3, and 4` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
41. Import data for `baseline absorbance of culture (day 2) measurements of cultures (0 hr timepoint)`, `0 hr absorbance timepoint measurements of plate 1`, `0 hr fluorescence timepoint measurements of plate 1`, `absorbance timepoint measurements of plate 1 at timepoints 2.0 hour, 4.0 hour, 6.0 hour`, `fluorescence timepoint measurements of plate 1 at timepoints 2.0 hour, 4.0 hour, 6.0 hour`, `absorbance timepoint measurements of Plates 2, 3, and 4`, `fluorescence timepoint measurements of Plates 2, 3, and 4` into provided Excel file.
---
Timestamp: 2022-06-28 22:07:54.510851---
Protocol version: 1.1b