# Cell measurement protocol

Challenging A - This version of the protocol involves 2 hr. time-point measurements using a plate-reader, but incubation may be performed inside a bench-top or standing incubator. 

Prior to performing the cell measurements you should perform all three of the calibration measurements. Please do not proceed unless you have completed the three calibration protocols. Completion of the calibrations will ensure that you understand the measurement process and that you can take the cell measurements under the same conditions. For the sake of consistency and reproducibility, we are requiring all teams to use E. coli K-12 DH5-alpha. If you do not have access to this strain, you can request streaks of the transformed devices from another team near you, and this can count as a collaboration as long as it is appropriately documented on both teams' wikis. If you are absolutely unable to obtain the DH5-alpha strain, you may still participate in the InterLab study by contacting the Measurement Committee (measurement at igem dot org) to discuss your situation.

For all of these cell measurements, you must use the same plates and volumes that you used in your calibration protocol. You must also use the same settings (e.g., filters or excitation and emission wavelengths) that you used in your calibration measurements. If you do not use the same plates, volumes, and settings, the measurements will not be valid.


## Protocol Outputs:
* `baseline absorbance of culture (day 2) measurements of cultures (0 hr timepoint)`
* `0 hr absorbance timepoint measurements of plate 1`
* `0 hr absorbance timepoint measurements of plate 1`
* `0 hr absorbance timepoint measurements of plate 1`
* `0 hr fluorescence timepoint measurements of plate 1`
* `0 hr fluorescence timepoint measurements of plate 1`
* `0 hr fluorescence timepoint measurements of plate 1`
* `2 hr absorbance timepoint measurements of plate 1`
* `2 hr fluorescence timepoint measurements of plate 1`
* `2 hr absorbance timepoint measurements of plate4`
* `2 hr fluorescence timepoint measurements of plate4`
* `4 hr absorbance timepoint measurements of plate 2`
* `4 hr fluorescence timepoint measurements of plate 2`
* `4 hr absorbance timepoint measurements of plate5`
* `4 hr fluorescence timepoint measurements of plate5`
* `6 hr absorbance timepoint measurements of plate 3`
* `6 hr fluorescence timepoint measurements of plate 3`
* `6 hr absorbance timepoint measurements of plate6`
* `6 hr fluorescence timepoint measurements of plate6`


## Protocol Materials:
* [_E. coli_ DH5 alpha](https://identifiers.org/pubchem.substance:24901740)
* [LB Broth+chloramphenicol](https://identifiers.org/pubchem.substance:24901740)
* [chloramphenicol](https://identifiers.org/pubchem.substance:24901740)
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
1. Transform `Negative control (J428100)` DNA into _`E. coli`_ ` DH5 alpha` and plate transformants on LB Broth+chloramphenicol. Repeat for the remaining transformant DNA:  `Positive control (I20270)`, `Test Device 1 (J364000)`, `Test Device 2 (J364001)`, `Test Device 3 (J364002)`, `Test Device 4 (J364007)`, `Test Device 5 (J364008)`, and `Test Device 6 (J364009)`.
2. Provision 16 x culture tubes to contain `culture (day 1)`
3. Inoculate _`E. coli`_ ` DH5 alpha+Negative control (J428100) transformant` into 5.0 milliliter of LB Broth+chloramphenicol in culture (day 1) and grow for 16.0 hour at 37.0 degree Celsius and 220.0 rpm.  Repeat this procedure for the other inocula:  _`E. coli`_ ` DH5 alpha+Positive control (I20270) transformant`, _`E. coli`_ ` DH5 alpha+Test Device 1 (J364000) transformant`, _`E. coli`_ ` DH5 alpha+Test Device 2 (J364001) transformant`, _`E. coli`_ ` DH5 alpha+Test Device 3 (J364002) transformant`, _`E. coli`_ ` DH5 alpha+Test Device 4 (J364007) transformant`, _`E. coli`_ ` DH5 alpha+Test Device 5 (J364008) transformant`, and _`E. coli`_ ` DH5 alpha+Test Device 6 (J364009) transformant`. Inoculate 2 replicates for each transformant, for a total of 16 cultures.
4. Provision 16 x culture tubes to contain `culture (day 2)`
5. Dilute each of 16 `culture (day 1)` samples with LB Broth+chloramphenicol into the culture tube at a 1:10 ratio and final volume of 10.0 milliliter. Maintain at 4.0 degree Celsius while performing dilutions.
6. Provision 16 x 1.5 mL microfuge tubes to contain `cultures (0 hr timepoint)`
7. Hold `cultures (0 hr timepoint)` at 4.0 degree Celsius. This will prevent cell growth while transferring samples.
8. Transfer 1.0 milliliter of each of 16 `culture (day 2)` samples to 1.5 mL microfuge tube containers to contain a total of 16 `cultures (0 hr timepoint)` samples. Maintain at 4.0 degree Celsius during transfer.
9. Measure baseline absorbance of culture (day 2) of `cultures (0 hr timepoint)` at 600.0 nanometer.
10. Provision 16 x 50 ml conical tubes to contain `back-diluted culture` The conical tube should be opaque, amber-colored, or covered with foil.
11. Back-dilute each of 16 `culture (day 2)` samples to a target OD of 0.02 using LB Broth+chloramphenicol as diluent to a final volume of 40.0 milliliter. Maintain at 4.0 degree Celsius while performing dilutions.

![](/Users/bbartley/Dev/git/sd2/paml/examples/fig1_cell_calibration.png)


12. Provision 16 x 50 ml conical tubes to contain `Tube 1` The conical tubes should be opaque, amber-colored, or covered with foil.
13. Provision 16 x 50 ml conical tubes to contain `Tube 2` The conical tubes should be opaque, amber-colored, or covered with foil.
14. Provision 16 x 50 ml conical tubes to contain `Tube 3` The conical tubes should be opaque, amber-colored, or covered with foil.
15. Transfer 1.0 milliliter of each of 16 `back-diluted culture` samples to 50 ml conical tube containers to contain a total of 16 `Tube 1` samples. Maintain at 4.0 degree Celsius during transfer.
16. Transfer 1.0 milliliter of each of 16 `back-diluted culture` samples to 50 ml conical tube containers to contain a total of 16 `Tube 2` samples. Maintain at 4.0 degree Celsius during transfer.
17. Transfer 1.0 milliliter of each of 16 `back-diluted culture` samples to 50 ml conical tube containers to contain a total of 16 `Tube 3` samples. Maintain at 4.0 degree Celsius during transfer.
18. Provision a 96 well microplate to contain `plate 1`
19. Provision a 96 well microplate to contain `plate 2`
20. Provision a 96 well microplate to contain `plate 3`
21. Hold `plate 1` at 4.0 degree Celsius.
22. Transfer 100.0 microliter of each `Tube 1` sample to 96 well microplate `plate 1` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
23. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate 1`. Maintain at 4.0 degree Celsius during transfer. These samples are blanks.
24. Transfer 100.0 microliter of each `Tube 2` sample to 96 well microplate `plate 2` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
25. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate 2`. Maintain at 4.0 degree Celsius during transfer. These samples are blanks.
26. Transfer 100.0 microliter of each `Tube 3` sample to 96 well microplate `plate 3` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
27. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate 1`. Maintain at 4.0 degree Celsius during transfer. These samples are blanks.

![](/Users/bbartley/Dev/git/sd2/paml/fig2_cell_calibration.png)


28. Cover `plate 1` samples in 96 well microplate with your choice of material to prevent evaporation.
29. Cover `plate 2` samples in 96 well microplate with your choice of material to prevent evaporation.
30. Cover `plate 3` samples in 96 well microplate with your choice of material to prevent evaporation.
31. Measure 0 hr absorbance timepoint of `plate 1` at 600.0 nanometer.
32. Measure 0 hr absorbance timepoint of `plate 1` at 600.0 nanometer.
33. Measure 0 hr absorbance timepoint of `plate 1` at 600.0 nanometer.
34. Measure 0 hr fluorescence timepoint of `plate 1` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
35. Measure 0 hr fluorescence timepoint of `plate 1` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
36. Measure 0 hr fluorescence timepoint of `plate 1` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
37. Incubate all `Tube 1` samples for 2.0 hour at 37.0 degree Celsius at 220.0 rpm.
38. Incubate all `plate 1` samples for 2.0 hour at 37.0 degree Celsius at 220.0 rpm.
39. Incubate all `Tube 2` samples for 4.0 hour at 37.0 degree Celsius at 220.0 rpm.
40. Incubate all `plate 2` samples for 4.0 hour at 37.0 degree Celsius at 220.0 rpm.
41. Incubate all `Tube 3` samples for 6.0 hour at 37.0 degree Celsius at 220.0 rpm.
42. Incubate all `plate 3` samples for 6.0 hour at 37.0 degree Celsius at 220.0 rpm.
43. Hold all `Tube 1` samples at 4.0 degree Celsius. This will inhibit cell growth during the subsequent pipetting steps.
44. Hold all `plate 1` samples at 4.0 degree Celsius. This will inhibit cell growth during the subsequent pipetting steps.
45. Provision a 96 well microplate to contain `plate4`
46. Transfer 100.0 microliter of each `Tube 1` sample to 96 well microplate `plate4` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
47. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate4`. Maintain at 4.0 degree Celsius during transfer. These samples are blanks.
48. Measure 2 hr absorbance timepoint of `plate 1` at 600.0 nanometer.
49. Measure 2 hr fluorescence timepoint of `plate 1` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
50. Measure 2 hr absorbance timepoint of `plate4` at 600.0 nanometer.
51. Measure 2 hr fluorescence timepoint of `plate4` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
52. Hold all `Tube 2` samples at 4.0 degree Celsius. This will inhibit cell growth during the subsequent pipetting steps.
53. Hold all `plate 2` samples at 4.0 degree Celsius. This will inhibit cell growth during the subsequent pipetting steps.
54. Provision a 96 well microplate to contain `plate5`
55. Transfer 100.0 microliter of each `Tube 2` sample to 96 well microplate `plate5` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
56. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate5`. Maintain at 4.0 degree Celsius during transfer. These samples are blanks.
57. Measure 4 hr absorbance timepoint of `plate 2` at 600.0 nanometer.
58. Measure 4 hr fluorescence timepoint of `plate 2` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
59. Measure 4 hr absorbance timepoint of `plate5` at 600.0 nanometer.
60. Measure 4 hr fluorescence timepoint of `plate5` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
61. Hold all `Tube 3` samples at 4.0 degree Celsius. This will inhibit cell growth during the subsequent pipetting steps.
62. Hold all `plate 3` samples at 4.0 degree Celsius. This will inhibit cell growth during the subsequent pipetting steps.
63. Provision a 96 well microplate to contain `plate6`
64. Transfer 100.0 microliter of each `Tube 3` sample to 96 well microplate `plate6` in the wells indicated in the plate layout.
 Maintain at 4.0 degree Celsius during transfer.
65. Transfer 100.0 microliter of `LB Broth+chloramphenicol` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate6`. Maintain at 4.0 degree Celsius during transfer. These samples are blanks.
66. Measure 6 hr absorbance timepoint of `plate 3` at 600.0 nanometer.
67. Measure 6 hr fluorescence timepoint of `plate 3` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
68. Measure 6 hr absorbance timepoint of `plate6` at 600.0 nanometer.
69. Measure 6 hr fluorescence timepoint of `plate6` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
70. Import data for `baseline absorbance of culture (day 2) measurements of cultures (0 hr timepoint)`, `0 hr absorbance timepoint measurements of plate 1`, `0 hr absorbance timepoint measurements of plate 1`, `0 hr absorbance timepoint measurements of plate 1`, `0 hr fluorescence timepoint measurements of plate 1`, `0 hr fluorescence timepoint measurements of plate 1`, `0 hr fluorescence timepoint measurements of plate 1`, `2 hr absorbance timepoint measurements of plate 1`, `2 hr fluorescence timepoint measurements of plate 1`, `2 hr absorbance timepoint measurements of plate4`, `2 hr fluorescence timepoint measurements of plate4`, `4 hr absorbance timepoint measurements of plate 2`, `4 hr fluorescence timepoint measurements of plate 2`, `4 hr absorbance timepoint measurements of plate5`, `4 hr fluorescence timepoint measurements of plate5`, `6 hr absorbance timepoint measurements of plate 3`, `6 hr fluorescence timepoint measurements of plate 3`, `6 hr absorbance timepoint measurements of plate6`, `6 hr fluorescence timepoint measurements of plate6` into provided Excel file.
---
Timestamp: 2022-06-25 09:48:10.927926---
Protocol version: 1.0b