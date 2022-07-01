# Cell measurement protocol

This year we plan to test protocols that will eventually be automated. For this reason, we will use 96-well plates instead of test tubes for culturing. Consequently, we want to evaluate how the performance of our plate culturing protocol compares to culturing in test tubes (e.g. 10 mL falcon tube) on a global scale.

At the end of the experiment, you will have two plates to be measured. You will measure both fluorescence and absorbance in each plate.

Before performing the cell measurements, you need to perform all the calibration measurements. Please do not proceed unless you have completed the calibration protocol. Completion of the calibrations will ensure that you understand the measurement process and that you can take the cell measurements under the same conditions. For consistency and reproducibility, we are requiring all teams to use E. coli K-12 DH5-alpha. If you do not have access to this strain, you can request streaks of the transformed devices from another team near you. If you are absolutely unable to obtain the DH5-alpha strain, you may still participate in the InterLab study by contacting the Engineering Committee (engineering [at] igem [dot] org) to discuss your situation.

For all below indicated cell measurements, you must use the same type of plates and the same volumes that you used in your calibration protocol. You must also use the same settings (e.g., filters or excitation and emission wavelengths) that you used in your calibration measurements. If you do not use the same type of plates, volumes, and settings, the measurements will not be valid.

Protocol summary: You will transform the eight devices listed in Table 1 into E. coli K-12 DH5-alpha cells. The next day you will pick two colonies from each transformation (16 total) and use them to inoculate 5 mL overnight cultures (this step is still in tubes). Each of these 16 overnight cultures will be used to inoculate four wells in a 96-well plate (200 microliters each, 4 replicates) or one test tube (12 mL). You will measure how fluorescence and optical density develops over 6 hours by taking measurements at time point 0 hour and at time point 6 hours. Follow the protocol below and the visual instructions in Figure 1 and Figure 2.


## Protocol Outputs:
* `baseline absorbance of culture (day 2) measurements of cultures (0 hr timepoint)`
* `0 hr absorbance timepoint measurements of plate 1`
* `0 hr fluorescence timepoint measurements of plate 1`
* `6 hr absorbance timepoint measurements of plate 1`
* `6 hr fluorescence timepoint measurements of plate 1`
* `6 hr absorbance timepoint measurements of plate 2`
* `6 hr fluorescence timepoint measurements of plate 2`


## Protocol Materials:
* [_E. coli_ DH5 alpha competent cells](https://identifiers.org/taxonomy:668369)
* [Negative control](http://parts.igem.org/Part:BBa_J428100)
* [Positive control (I20270)](http://parts.igem.org/Part:BBa_I20270)
* [Test Device 1 (J364000)](http://parts.igem.org/Part:BBa_J364000)
* [Test Device 2 (J36401)](http://parts.igem.org/Part:BBa_J364001)
* [Test Device 3 (J36402)](http://parts.igem.org/Part:BBa_J364002)
* [Test Device 4 (J364007)](http://parts.igem.org/Part:BBa_J364007)
* [Test Device 5 (J364008)](http://parts.igem.org/Part:BBa_J364008)
* [Test Device 6 (J364009)](http://parts.igem.org/Part:BBa_J364009)
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
* 96 well microplate (x 2)
* microplate adhesive sealing film


#### Table 1: Part Locations in Distribution Kit
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
1. Obtain 8 x Petri dish containing LB Agar + Chloramphenicol (34 ug/mL) growth medium for culturing `transformant strains`
2. Transform `Negative control` DNA into _`E. coli`_ ` DH5 alpha competent cells` and plate transformants on LB Broth + Chloramphenicol (34 ug/mL). Repeat for the remaining transformant DNA:  `Positive control (I20270)`, `Test Device 1 (J364000)`, `Test Device 2 (J36401)`, `Test Device 3 (J36402)`, `Test Device 4 (J364007)`, `Test Device 5 (J364008)`, and `Test Device 6 (J364009)`. Plate transformants on `transformant strains` plates. Incubate at 37.0°C for 16.0 hour (overnight).
3. Obtain 16 x culture tubes to contain `culture (day 1)`
4. Pick 2 colonies from each `transformant strains` plate.
5. Inoculate 2 colonies of each transformant transformant strains, for a total of 16 cultures. Inoculate each into 5.0 mL of LB Broth + Chloramphenicol (34 ug/mL) in culture (day 1) and grow for 16.0 hour at 37.0°C and 220 rpm.
6. Obtain 16 x culture tubes to contain `culture (day 2)`
7. Dilute each of 16 `culture (day 1)` samples with LB Broth + Chloramphenicol (34 ug/mL) into the culture tube at a 1:10 ratio and final volume of 5.0 mL. Maintain at 4.0°C while performing dilutions. (This can be also performed on ice).
8. Obtain 16 x 1.5 mL microfuge tubes to contain `cultures (0 hr timepoint)`
9. Hold `cultures (0 hr timepoint)` on ice. This will prevent cell growth while transferring samples.
10. Transfer 1.0 mL of each of 16 `culture (day 2)` samples to 1.5 mL microfuge tube containers to contain a total of 16 `cultures (0 hr timepoint)` samples. Maintain at 4.0°C during transfer. (This can be also performed on Ice).
11. Measure baseline absorbance of culture (day 2) of `cultures (0 hr timepoint)` at 600.0 nanometer.
12. Obtain 16 x 50 ml conical tubes to contain `back-diluted culture` The conical tube should be opaque, amber-colored, or covered with foil.
13. Back-dilute each of 16 `culture (day 2)` samples to a target OD of 0.02 using LB Broth + Chloramphenicol (34 ug/mL) as diluent to a final volume of 12.0 mL. Maintain at 4.0°C while performing dilutions.

![](/Users/bbartley/Dev/git/sd2/paml/examples/fig1_standard_protocol.png)
<p align="center">Fig 1: Visual representation of protocol</p>

14. Obtain 16 x 1.5 mL microfuge tubes to contain `back-diluted culture aliquots`
15. Hold `back-diluted culture aliquots` on ice. This will prevent cell growth while transferring samples.
16. Transfer 1.0 mL of each of 16 `back-diluted culture` samples to 1.5 mL microfuge tube containers to contain a total of 16 `back-diluted culture aliquots` samples. Maintain at 4.0°C during transfer. (This can be also performed on Ice).
17. Obtain a 96 well microplate to contain `plate 1`
18. Hold `plate 1` on ice.
19. Transfer 200.0 microliter of each `back-diluted culture aliquots` sample to 96 well microplate `plate 1` in the wells indicated in the plate layout.
 Maintain at 4.0°C during transfer.
20. Transfer 200.0 microliter of `LB Broth + Chloramphenicol (34 ug/mL)` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate 1`. Maintain at 4.0°C during transfer. These samples are blanks.

![](/Users/bbartley/Dev/git/sd2/paml/examples/fig2_cell_calibration.png)
<p align="center">Fig 2: Plate layout</p>

21. Measure 0 hr absorbance timepoint of `plate 1` at 600.0 nanometer.
22. Measure 0 hr fluorescence timepoint of `plate 1` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
23. Cover `plate 1` samples in 96 well microplate with your choice of material to prevent evaporation.
24. Incubate all `back-diluted culture` samples for 6.0 hour at 37.0°C at 220 rpm.
25. Incubate all `plate 1` samples for 6.0 hour at 37.0°C at 220 rpm.
26. Hold all `back-diluted culture` samples on ice. This will inhibit cell growth during the subsequent pipetting steps.
27. Hold all `plate 1` samples on ice. This will inhibit cell growth during the subsequent pipetting steps.
28. Obtain a 96 well microplate to contain `plate 2`
29. Hold `plate 2` on ice.
30. Transfer 200.0 microliter of each `back-diluted culture` sample to 96 well microplate `plate 2` in the wells indicated in the plate layout.
 Maintain at 4.0°C during transfer.
31. Transfer 200.0 microliter of `LB Broth + Chloramphenicol (34 ug/mL)` sample to wells A1:H1, A10:H10, A12:H12 of  96 well microplate `plate 2`. Maintain at 4.0°C during transfer. These are the blanks.
32. Measure 6 hr absorbance timepoint of `plate 1` at 600.0 nanometer.
33. Measure 6 hr fluorescence timepoint of `plate 1` with excitation wavelength of 485.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
34. Measure 6 hr absorbance timepoint of `plate 2` at 600.0 nanometer.
35. Measure 6 hr fluorescence timepoint of `plate 2` with excitation wavelength of 485.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
36. Import data for `baseline absorbance of culture (day 2) measurements of cultures (0 hr timepoint)`, `0 hr absorbance timepoint measurements of plate 1`, `0 hr fluorescence timepoint measurements of plate 1`, `6 hr absorbance timepoint measurements of plate 1`, `6 hr fluorescence timepoint measurements of plate 1`, `6 hr absorbance timepoint measurements of plate 2`, `6 hr fluorescence timepoint measurements of plate 2` into provided Excel file.
---
Timestamp: 2022-07-01 09:48:31.650433---
Protocol version: 1.2.1