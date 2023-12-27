# Multicolor fluorescence per bacterial particle calibration


Plate readers report fluorescence values in arbitrary units that vary widely from instrument to instrument. Therefore absolute fluorescence values cannot be directly compared from one instrument to another. In order to compare fluorescence output of biological devices, it is necessary to create a standard fluorescence curve. This variant of the protocol uses two replicates of three colors of dye, plus beads.
Adapted from [https://dx.doi.org/10.17504/protocols.io.bht7j6rn](https://dx.doi.org/10.17504/protocols.io.bht7j6r) and [https://dx.doi.org/10.17504/protocols.io.6zrhf56](https://dx.doi.org/10.17504/protocols.io.6zrhf56)
    


## Protocol Inputs:
* `source`
* `destination`
* `amount`
* `source`
* `destination`
* `amount`
* `source`
* `destination`
* `amount`
* `source`
* `destination`
* `amount`


## Protocol Outputs:
* Dataset: [multicolor-particle-calibration.xlsx](multicolor-particle-calibration.xlsx)


## Protocol Materials:
* [Cascade Blue](https://pubchem.ncbi.nlm.nih.gov/substance/57269662)
* [Water, sterile-filtered, BioReagent, suitable for cell culture](https://identifiers.org/pubchem.substance:24901740)
* [Fluorescein](https://pubchem.ncbi.nlm.nih.gov/substance/329753341)
* [Phosphate Buffered Saline](https://pubchem.ncbi.nlm.nih.gov/compound/24978514)
* [NanoCym 950 nm monodisperse silica nanoparticles](https://nanocym.com/wp-content/uploads/2018/07/NanoCym-All-Datasheets-.pdf)
* [Sulforhodamine](https://pubchem.ncbi.nlm.nih.gov/compound/139216224)
* stock reagent container (x 6)
* waste container
* 96 well microplate


## Protocol Steps:
1. Provision a container named `Fluorescein calibrant` such as: 
	[StockReagent](https://sift.net/container-ontology/container-ontology#StockReagent).
2. Provision a container named `Sulforhodamine 101 calibrant` such as: 
	[StockReagent](https://sift.net/container-ontology/container-ontology#StockReagent).
3. Provision a container named `Cascade blue calibrant` such as: 
	[StockReagent](https://sift.net/container-ontology/container-ontology#StockReagent).
4. Provision a container named `microspheres` such as: 
	[StockReagent](https://sift.net/container-ontology/container-ontology#StockReagent).
5. Provision a container named `molecular grade H2O` such as: 
	[StockReagent](https://sift.net/container-ontology/container-ontology#StockReagent).
6. Provision a container named `PBS` such as: 
	[StockReagent](https://sift.net/container-ontology/container-ontology#StockReagent).
7. Provision a container named `discard` such as: 
	[WasteContainer](https://sift.net/container-ontology/container-ontology#WasteContainer).
8. Pipette 12.0 milliliter of [Water, sterile-filtered, BioReagent, suitable for cell culture](https://identifiers.org/pubchem.substance:24901740) into `molecular grade H2O`.
9. Pipette 12.0 milliliter of [Phosphate Buffered Saline](https://pubchem.ncbi.nlm.nih.gov/compound/24978514) into `PBS`.
10. Pipette 500.0 microliter of [Fluorescein](https://pubchem.ncbi.nlm.nih.gov/substance/329753341) into `Fluorescein calibrant`.
11. Pipette 500.0 microliter of [Cascade Blue](https://pubchem.ncbi.nlm.nih.gov/substance/57269662) into `Cascade blue calibrant`.
12. Pipette 500.0 microliter of [Sulforhodamine](https://pubchem.ncbi.nlm.nih.gov/compound/139216224) into `Sulforhodamine 101 calibrant`.
13. Pipette 500.0 microliter of [NanoCym 950 nm monodisperse silica nanoparticles](https://nanocym.com/wp-content/uploads/2018/07/NanoCym-All-Datasheets-.pdf) into `microspheres`.
14. Transfer 1.0 milliliter of `PBS` sample to  stock reagent container `Fluorescein calibrant`.
15. Vortex `PBS`.
16. Transfer 1.0 milliliter of `PBS` sample to  stock reagent container `Sulforhodamine 101 calibrant`.
17. Vortex `PBS`.
18. Transfer 1.0 milliliter of `molecular grade H2O` sample to  stock reagent container `Cascade blue calibrant`.
19. Vortex `molecular grade H2O`.
20. Transfer 1.0 milliliter of `molecular grade H2O` sample to  stock reagent container `microspheres`.
21. Vortex `molecular grade H2O`.
22. Provision a container named `calibration plate` such as: 
	[Corning96WellPlate360uLFlat](https://sift.net/container-ontology/container-ontology#Corning96WellPlate360uLFlat).
23. Transfer 100.0 microliter of `PBS` sample to wells A2:D12 of 96 well microplate `calibration plate`.
24. Transfer 100.0 microliter of `molecular grade H2O` sample to wells E2:H12 of 96 well microplate `calibration plate`.
25. Transfer 200.0 microliter of `Fluorescein calibrant` sample to wells A1 of 96 well microplate `calibration plate`.
26. Transfer 200.0 microliter of `Fluorescein calibrant` sample to wells B1 of 96 well microplate `calibration plate`.
27. Transfer 200.0 microliter of `Sulforhodamine 101 calibrant` sample to wells C1 of 96 well microplate `calibration plate`.
28. Transfer 200.0 microliter of `Sulforhodamine 101 calibrant` sample to wells D1 of 96 well microplate `calibration plate`.
29. Transfer 200.0 microliter of `Cascade blue calibrant` sample to wells E1 of 96 well microplate `calibration plate`.
30. Transfer 200.0 microliter of `Cascade blue calibrant` sample to wells F1 of 96 well microplate `calibration plate`.
31. Transfer 200.0 microliter of `microspheres` sample to wells G1 of 96 well microplate `calibration plate`.
32. Transfer 200.0 microliter of `microspheres` sample to wells H1 of 96 well microplate `calibration plate`.

![](../figures/serial_dilution.png)
<p align="center">Serial Dilution</p>

33. Transfer 100.0 microliter of `calibration plate` sample to  waste container `discard`.  This step ensures that all wells contain an equivalent volume. Be sure to change pipette tips for every well to avoid cross-contamination.
34. Transfer 100.0 microliter of `PBS` sample to wells A1:D12 of 96 well microplate `calibration plate`.  This will bring all wells to volume 200 microliter.
35. Transfer 100.0 microliter of `molecular grade H2O` sample to wells E1:H12 of 96 well microplate `calibration plate`.  This will bring all wells to volume 200 microliter.
36. Measure fluorescein and bead fluorescence of `calibration plate` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
37. Measure sulforhodamine 101 fluorescence of `calibration plate` with excitation wavelength of 561.0 nanometer and emission filter of 610.0 nanometer and 20.0 nanometer bandpass.
38. Measure cascade blue fluorescence of `calibration plate` with excitation wavelength of 405.0 nanometer and emission filter of 450.0 nanometer and 50.0 nanometer bandpass.
39. Measure absorbance of `calibration plate` at 600.0 nanometer.
40. Import data into the provided Excel file: Dataset: [multicolor-particle-calibration.xlsx](multicolor-particle-calibration.xlsx).

---
Timestamp: 2023-05-27 13:47:09.222419
Protocol version: v1.0a2-197-g672c9bc

