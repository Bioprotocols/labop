# Multicolor fluorescence per bacterial particle calibration

Plate readers report fluorescence values in arbitrary units that vary widely from instrument to instrument. Therefore absolute fluorescence values cannot be directly compared from one instrument to another. In order to compare fluorescence output of biological devices, it is necessary to create a standard fluorescence curve. This variant of the protocol uses two replicates of three colors of dye, plus beads.
Adapted from [https://dx.doi.org/10.17504/protocols.io.bht7j6rn](https://dx.doi.org/10.17504/protocols.io.bht7j6r) and [https://dx.doi.org/10.17504/protocols.io.6zrhf56](https://dx.doi.org/10.17504/protocols.io.6zrhf56)


## Protocol Outputs:
* Dataset: [multicolor-particle-calibration.xlsx](multicolor-particle-calibration.xlsx)


## Protocol Materials:
* [Water, sterile-filtered, BioReagent, suitable for cell culture](https://identifiers.org/pubchem.substance:24901740)
* [NanoCym 950 nm monodisperse silica nanoparticles](https://nanocym.com/wp-content/uploads/2018/07/NanoCym-All-Datasheets-.pdf)
* [Phosphate Buffered Saline](https://pubchem.ncbi.nlm.nih.gov/substance/329753341)
* [Fluorescein](https://pubchem.ncbi.nlm.nih.gov/substance/329753341)
* [Cascade Blue](https://pubchem.ncbi.nlm.nih.gov/substance/329753341)
* [Sulforhodamine](https://pubchem.ncbi.nlm.nih.gov/substance/329753341)
* stock reagent container (x 4)
* 96 well plate


## Protocol Steps:
1. Provision the stock reagent container containing `Fluorescein calibrant`.
2. Provision the stock reagent container containing `Sulforhodamine 101 calibrant`.
3. Provision the stock reagent container containing `Cascade blue calibrant`.
4. Provision the stock reagent container containing `NanoCym 950 nm microspheres`.
5. Transfer 1.0 milliliter of `Phosphate Buffered Saline` sample to  stock reagent container `Fluorescein calibrant`. The reconstituted `Fluorescein` should have a final concentration of 10 uM in `Phosphate Buffered Saline`.
6. Vortex `Fluorescein calibrant`.
7. Transfer 1.0 milliliter of `Phosphate Buffered Saline` sample to  stock reagent container `Sulforhodamine 101 calibrant`. The reconstituted `Sulforhodamine` standard will have a final concentration of 2 uM in `Phosphate Buffered Saline`.
8. Vortex `Sulforhodamine 101 calibrant`.
9. Transfer 1.0 milliliter of `Water, sterile-filtered, BioReagent, suitable for cell culture` sample to  stock reagent container `Cascade blue calibrant`. The reconstituted `Cascade Blue` calibrant will have a final concentration of 10 uM in `Water, sterile-filtered, BioReagent, suitable for cell culture`.
10. Vortex `Cascade blue calibrant`.
11. Transfer 1.0 milliliter of `Water, sterile-filtered, BioReagent, suitable for cell culture` sample to  stock reagent container `NanoCym 950 nm microspheres`. The resuspended `NanoCym 950 nm monodisperse silica nanoparticles` will have a final concentration of 3e9 microspheres/mL in `Water, sterile-filtered, BioReagent, suitable for cell culture`.
12. Vortex `NanoCym 950 nm microspheres`.
13. Provision a container named `calibration plate` such as: 
	[NEST96WellPlate](https://sift.net/container-ontology/container-ontology#NEST96WellPlate),
	[Corning96WellPlate360uLFlat](https://sift.net/container-ontology/container-ontology#Corning96WellPlate360uLFlat).
14. Transfer 100.0 microliter of `Phosphate Buffered Saline` sample to wells A2:D12 of 96 well plate `calibration plate`.
15. Transfer 100.0 microliter of `Water, sterile-filtered, BioReagent, suitable for cell culture` sample to wells E2:H12 of 96 well plate `calibration plate`.
16. Transfer 200.0 microliter of `Fluorescein calibrant` sample to wells A1 of 96 well plate `calibration plate`.
17. Transfer 200.0 microliter of `Fluorescein calibrant` sample to wells B1 of 96 well plate `calibration plate`.
18. Transfer 200.0 microliter of `Sulforhodamine 101 calibrant` sample to wells C1 of 96 well plate `calibration plate`.
19. Transfer 200.0 microliter of `Sulforhodamine 101 calibrant` sample to wells D1 of 96 well plate `calibration plate`.
20. Transfer 200.0 microliter of `Cascade blue calibrant` sample to wells E1 of 96 well plate `calibration plate`.
21. Transfer 200.0 microliter of `Cascade blue calibrant` sample to wells F1 of 96 well plate `calibration plate`.
22. Transfer 200.0 microliter of `NanoCym 950 nm microspheres` sample to wells G1 of 96 well plate `calibration plate`.
23. Transfer 200.0 microliter of `NanoCym 950 nm microspheres` sample to wells H1 of 96 well plate `calibration plate`.
24. Perform a series of 10 2-fold dilutions on A1 using `Phosphate Buffered Saline` as diluent to a final volume of 100.0 microliter in wells A1:A11 of 96 well plate `calibration plate`.  For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.

![](../figures/serial_dilution.png)
<p align="center">Serial Dilution</p>

25. Perform a series of 10 2-fold dilutions on B1 using `Phosphate Buffered Saline` as diluent to a final volume of 100.0 microliter in wells B1:B11 of 96 well plate `calibration plate`.  For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
26. Perform a series of 10 2-fold dilutions on C1 using `Phosphate Buffered Saline` as diluent to a final volume of 100.0 microliter in wells C1:C11 of 96 well plate `calibration plate`.  For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
27. Perform a series of 10 2-fold dilutions on D1 using `Phosphate Buffered Saline` as diluent to a final volume of 100.0 microliter in wells D1:D11 of 96 well plate `calibration plate`.  For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
28. Perform a series of 10 2-fold dilutions on E1 using `Water, sterile-filtered, BioReagent, suitable for cell culture` as diluent to a final volume of 100.0 microliter in wells E1:E11 of 96 well plate `calibration plate`.  For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
29. Perform a series of 10 2-fold dilutions on F1 using `Water, sterile-filtered, BioReagent, suitable for cell culture` as diluent to a final volume of 100.0 microliter in wells F1:F11 of 96 well plate `calibration plate`.  For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
30. Perform a series of 10 2-fold dilutions on G1 using `Water, sterile-filtered, BioReagent, suitable for cell culture` as diluent to a final volume of 100.0 microliter in wells G1:G11 of 96 well plate `calibration plate`.  For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
31. Perform a series of 10 2-fold dilutions on H1 using `Water, sterile-filtered, BioReagent, suitable for cell culture` as diluent to a final volume of 100.0 microliter in wells H1:H11 of 96 well plate `calibration plate`.  For each transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
32. Discard 100.0 microliter from wells A11:H11 of 96 well plate `calibration plate`.  This step ensures that all wells contain an equivalent volume. Be sure to change pipette tips for every well to avoid cross-contamination
33. Transfer 100.0 microliter of `Phosphate Buffered Saline` sample to wells A1:D12 of 96 well plate `calibration plate`.  This will bring all wells to volume 200 microliter.
34. Transfer 100.0 microliter of `Water, sterile-filtered, BioReagent, suitable for cell culture` sample to wells E1:H12 of 96 well plate `calibration plate`.  This will bring all wells to volume 200 microliter.
35. Measure fluorescein and bead fluorescence of `calibration plate` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
36. Measure sulforhodamine 101 fluorescence of `calibration plate` with excitation wavelength of 561.0 nanometer and emission filter of 610.0 nanometer and 20.0 nanometer bandpass.
37. Measure cascade blue fluorescence of `calibration plate` with excitation wavelength of 405.0 nanometer and emission filter of 450.0 nanometer and 50.0 nanometer bandpass.
38. Measure absorbance of `calibration plate` at 600.0 nanometer.
39. Import data into the provided Excel file: Dataset: [multicolor-particle-calibration.xlsx](multicolor-particle-calibration.xlsx).
---
Timestamp: 2023-03-29 12:51:00.810801
Protocol version: 1.2
