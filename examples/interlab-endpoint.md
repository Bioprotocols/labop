# Cell measurement protocol

This year we plan to go towards automation, where a 96-well plate instead of a tube is used for culturing. Prior to the full establishment of this protocol, we need to evaluate how the performance is worldwide with this as well as with parallel experiment in the test tube, which has been used as standard culturing protocol.

At the end of the experiment, you would have two plates to be measured (five for challenging version). You will measure both fluorescence and absorbance in each plate.

Prior to performing the cell measurements you should perform all three of the calibration measurements. Please do not proceed unless you have completed the three calibration protocols. Completion of the calibrations will ensure that you understand the measurement process and that you can take the cell measurements under the same conditions. For the sake of consistency and reproducibility, we are requiring all teams to use E. coli K-12 DH5-alpha. If you do not have access to this strain, you can request streaks of the transformed devices from another team near you, and this can count as a collaboration as long as it is appropriately documented on both teams' wikis. If you are absolutely unable to obtain the DH5-alpha strain, you may still participate in the InterLab study by contacting the Measurement Committee (measurement at igem dot org) to discuss your situation.

For all of these cell measurements, you must use the same plates and volumes that you used in your calibration protocol. You must also use the same settings (e.g., filters or excitation and emission wavelengths) that you used in your calibration measurements. If you do not use the same plates, volumes, and settings, the measurements will not be valid.


## Protocol Outputs:
* `baseline absorbance of culture (day 2) measurements of cultures (0 hr timepoint)`
* `0 hr absorbance timepoint measurements of plate 1`
* `0 hr fluorescence timepoint measurements of plate 1`
* `6 hr absorbance timepoint measurements of plate 1`
* `6 hr fluorescence timepoint measurements of plate 1`
* `6 hr absorbance timepoint measurements of plate 2`
* `6 hr fluorescence timepoint measurements of plate 2`


## Protocol Materials:
* [_E. coli_ DH5 alpha](https://identifiers.org/pubchem.substance:24901740)
* [LB Broth+chloramphenicol](https://identifiers.org/pubchem.substance:24901740)
* [chloramphenicol](https://identifiers.org/pubchem.substance:24901740)
* [Negative control](http://parts.igem.org/Part:BBa_J428100)
* [Positive control (I20270)](http://parts.igem.org/Part:BBa_I20270)
* [Test Device 1 (J364000)](http://parts.igem.org/Part:BBa_J364000)
* [Test Device 2 (J36401)](http://parts.igem.org/Part:BBa_J364001)
* [Test Device 3 (J36402)](http://parts.igem.org/Part:BBa_J364002)
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
1. Transform `Negative control` DNA into _`E. coli`_ ` DH5 alpha` and plate transformants on LB Broth+chloramphenicol. Repeat for the remaining transformant DNA:  `Positive control (I20270)`, `Test Device 1 (J364000)`, `Test Device 2 (J36401)`, `Test Device 3 (J36402)`, `Test Device 4 (J364007)`, `Test Device 5 (J364008)`, and `Test Device 6 (J364009)`.
2. Provision 16 x culture tubes to contain `culture (day 1)`
3. Inoculate _`E. coli`_ ` DH5 alpha+Negative control transformant` into 5.0 milliliter of LB Broth+chloramphenicol in culture (day 1) and grow for 16.0 hour at 37.0 degree Celsius and 220.0 rpm.  Repeat this procedure for the other inocula:  _`E. coli`_ ` DH5 alpha+Positive control (I20270) transformant`, _`E. coli`_ ` DH5 alpha+Test Device 1 (J364000) transformant`, _`E. coli`_ ` DH5 alpha+Test Device 2 (J36401) transformant`, _`E. coli`_ ` DH5 alpha+Test Device 3 (J36402) transformant`, _`E. coli`_ ` DH5 alpha+Test Device 4 (J364007) transformant`, _`E. coli`_ ` DH5 alpha+Test Device 5 (J364008) transformant`, and _`E. coli`_ ` DH5 alpha+Test Device 6 (J364009) transformant`. Inoculate 2 replicates for each transformant, for a total of 16 cultures.
4. Provision 16 x culture tubes to contain `culture (day 2)`
5. Dilute each of 16 `culture (day 1)` samples with LB Broth+chloramphenicol into the culture tube at a 1:10 ratio and final volume of 5.0 milliliter. Maintain at 4.0 degree Celsius while performing dilutions.
6. Provision 16 x 1.5 mL microfuge tubes to contain `cultures (0 hr timepoint)`
7. Hold `cultures (0 hr timepoint)` at 4.0 degree Celsius. This will prevent cell growth while transferring samples.
8. Transfer 1.0 milliliter of each of 16 `culture (day 2)` samples to 1.5 mL microfuge tube containers to contain a total of 16 `cultures (0 hr timepoint)` samples. Maintain at 4.0 degree Celsius during transfer.
9. Measure baseline absorbance of culture (day 2) of `cultures (0 hr timepoint)` at 600.0 nanometer.
10. Provision 16 x 50 ml conical tubes to contain `back-diluted culture` The conical tube should be opaque, amber-colored, or covered with foil.
11. Back-dilute each of 16 `culture (day 2)` samples to a target OD of 0.02 using LB Broth+chloramphenicol as diluent to a final volume of 12.0 milliliter. Maintain at 4.0 degree Celsius while performing dilutions.

![](/Users/bbartley/Dev/git/sd2/paml/examples/fig1_cell_calibration.png)


12. Provision 16 x 1.5 mL microfuge tubes to contain `back-diluted culture aliquots`
13. Hold `back-diluted culture aliquots` at 4.0 degree Celsius. This will prevent cell growth while transferring samples.
14. Transfer 1.0 milliliter of each of 16 `back-diluted culture` samples to 1.5 mL microfuge tube containers to contain a total of 16 `back-diluted culture aliquots` samples. Maintain at 4.0 degree Celsius during transfer.
15. Provision a 96 well microplate to contain `plate 1`
16. Hold `plate 1` at 4.0 degree Celsius.
17. Transfer 100.0 microliter of each `cultures (0 hr timepoint)` sample to 96 well microplate `plate 1` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
18. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate 1`. Maintain at 4.0 degree Celsius during transfer. These samples are blanks.

![](/Users/bbartley/Dev/git/sd2/paml/fig2_cell_calibration.png)


19. Cover `plate 1` samples in 96 well microplate with your choice of material to prevent evaporation.
20. Measure 0 hr absorbance timepoint of `plate 1` at 600.0 nanometer.
21. Measure 0 hr fluorescence timepoint of `plate 1` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
22. Incubate all `back-diluted culture` samples for 6.0 hour at 37.0 degree Celsius at 220.0 rpm.
23. Incubate all `plate 1` samples for 6.0 hour at 37.0 degree Celsius at 220.0 rpm.
24. Hold all `cultures (0 hr timepoint)` samples at 4.0 degree Celsius. This will inhibit cell growth during the subsequent pipetting steps.
25. Hold all `plate 1` samples at 4.0 degree Celsius. This will inhibit cell growth during the subsequent pipetting steps.
26. Provision 16 x 1.5 mL microfuge tubes to contain `6hr timepoint`
27. Provision a 96 well microplate to contain `plate 2`
28. Hold `6hr timepoint` at 4.0 degree Celsius. This will prevent cell growth while transferring samples.
29. Hold `plate 2` at 4.0 degree Celsius.
30. Transfer 1.0 milliliter of each of 16 `back-diluted culture` samples to 1.5 mL microfuge tube containers to contain a total of 16 `6hr timepoint` samples. Maintain at 4.0 degree Celsius during transfer.
31. Transfer 100.0 microliter of each `6hr timepoint` sample to 96 well microplate `plate 2` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
32. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate 2`. Maintain at 4.0 degree Celsius during transfer. These are the blanks.
33. Cover `plate 1` samples in 96 well microplate with your choice of material to prevent evaporation.
34. Measure 6 hr absorbance timepoint of `plate 1` at 600.0 nanometer.
35. Measure 6 hr fluorescence timepoint of `plate 1` with excitation wavelength of 485.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
36. Measure 6 hr absorbance timepoint of `plate 2` at 600.0 nanometer.
37. Measure 6 hr fluorescence timepoint of `plate 2` with excitation wavelength of 485.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
38. Import data for `baseline absorbance of culture (day 2) measurements of cultures (0 hr timepoint)`, `0 hr absorbance timepoint measurements of plate 1`, `0 hr fluorescence timepoint measurements of plate 1`, `6 hr absorbance timepoint measurements of plate 1`, `6 hr fluorescence timepoint measurements of plate 1`, `6 hr absorbance timepoint measurements of plate 2`, `6 hr fluorescence timepoint measurements of plate 2` into provided Excel file.
---
Timestamp: 2022-06-25 09:44:22.443625---
Protocol version: 1.0b