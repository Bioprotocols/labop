# Multicolor fluorescence per bacterial particle calibration


Plate readers report fluorescence values in arbitrary units that vary widely from instrument to instrument. Therefore absolute fluorescence values cannot be directly compared from one instrument to another. In order to compare fluorescence output of biological devices, it is necessary to create a standard fluorescence curve. This variant of the protocol uses two replicates of three colors of dye, plus beads.
Adapted from [https://dx.doi.org/10.17504/protocols.io.bht7j6rn](https://dx.doi.org/10.17504/protocols.io.bht7j6r) and [https://dx.doi.org/10.17504/protocols.io.6zrhf56](https://dx.doi.org/10.17504/protocols.io.6zrhf56)
    


## Protocol Inputs:
* `specification`
* `reagent`
* `reagent_mass`
* `buffer`
* `buffer_volume`
* `buffer_container`
* `source`
* `destination`
* `amount`
* `specification`
* `reagent`
* `reagent_mass`
* `buffer`
* `buffer_volume`
* `buffer_container`
* `source`
* `destination`
* `amount`


## Protocol Outputs:
* Dataset: [singlecolor-particle-calibration.xlsx](singlecolor-particle-calibration.xlsx)
* `ddh2o_container`
* `pbs_container`
* `samples`
* `fluorescein_standard_solution_container`
* `samples`
* `microsphere_standard_solution_container`


## Protocol Materials:
* [Water, sterile-filtered, BioReagent, suitable for cell culture](https://identifiers.org/pubchem.substance:24901740)
* [Fluorescein](https://pubchem.ncbi.nlm.nih.gov/substance/329753341)
* [Phosphate Buffered Saline](https://pubchem.ncbi.nlm.nih.gov/compound/24978514)
* [NanoCym 950 nm monodisperse silica nanoparticles](https://nanocym.com/wp-content/uploads/2018/07/NanoCym-All-Datasheets-.pdf)
* 50mL stock reagent container (x 2)
* stock reagent container (x 2)
* 96 well microplate
* waste container


## Protocol Steps:
1. Provision a container named `molecular grade H2O` such as: 
	[StockReagent50mL](https://sift.net/container-ontology/container-ontology#StockReagent50mL).
2. Pipette 12.0 milliliter of [Water, sterile-filtered, BioReagent, suitable for cell culture](https://identifiers.org/pubchem.substance:24901740) into `molecular grade H2O`.
3. Provision a container named `PBS` such as: 
	[StockReagent50mL](https://sift.net/container-ontology/container-ontology#StockReagent50mL).
4. Pipette 12.0 milliliter of [Phosphate Buffered Saline](https://pubchem.ncbi.nlm.nih.gov/compound/24978514) into `PBS`.
5. Provision a container named `Fluorescein calibrant` such as: 
	[StockReagent](https://sift.net/container-ontology/container-ontology#StockReagent).
6. Pipette 5.6441 microgram of [Fluorescein](https://pubchem.ncbi.nlm.nih.gov/substance/329753341) into `Fluorescein calibrant`.
7. Transfer 1.5 milliliter of `PBS` sample to  stock reagent container `Fluorescein calibrant`.
8. Vortex `Fluorescein calibrant`.
9. Provision a container named `microspheres` such as: 
	[StockReagent](https://sift.net/container-ontology/container-ontology#StockReagent).
10. Pipette 1.26 milligram of [NanoCym 950 nm monodisperse silica nanoparticles](https://nanocym.com/wp-content/uploads/2018/07/NanoCym-All-Datasheets-.pdf) into `microspheres`.
11. Transfer 1.5 milliliter of `molecular grade H2O` sample to  stock reagent container `microspheres`.
12. Vortex `microspheres`.
13. Provision a container named `discard` such as: 
	[WasteContainer](https://sift.net/container-ontology/container-ontology#WasteContainer).
14. Provision a container named `calibration plate` such as: 
	[Corning96WellPlate360uLFlat](https://sift.net/container-ontology/container-ontology#Corning96WellPlate360uLFlat).
15. Transfer 100.0 microliter of `PBS` sample to wells A2:D12 of 96 well microplate `calibration plate`.
16. Transfer 100.0 microliter of `molecular grade H2O` sample to wells E2:H12 of 96 well microplate `calibration plate`.
17. Transfer 200.0 microliter of `Fluorescein calibrant` sample to wells A1 of 96 well microplate `calibration plate`.
18. Transfer 200.0 microliter of `Fluorescein calibrant` sample to wells B1 of 96 well microplate `calibration plate`.
19. Transfer 200.0 microliter of `Fluorescein calibrant` sample to wells C1 of 96 well microplate `calibration plate`.
20. Transfer 200.0 microliter of `Fluorescein calibrant` sample to wells D1 of 96 well microplate `calibration plate`.
21. Transfer 200.0 microliter of `microspheres` sample to wells E1 of 96 well microplate `calibration plate`.
22. Transfer 200.0 microliter of `microspheres` sample to wells F1 of 96 well microplate `calibration plate`.
23. Transfer 200.0 microliter of `microspheres` sample to wells G1 of 96 well microplate `calibration plate`.
24. Transfer 200.0 microliter of `microspheres` sample to wells H1 of 96 well microplate `calibration plate`.
25. Perform a series of 10 2-fold dilutions on A1:A11 96 well microplate `calibration plate`. Start with A1 and end with a final excess volume of 100.0 microliter in A11.  For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.

![](../figures/serial_dilution.png)
<p align="center">Serial Dilution</p>

26. Perform a series of 10 2-fold dilutions on B1:B11 96 well microplate `calibration plate`. Start with B1 and end with a final excess volume of 100.0 microliter in B11.  For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
27. Perform a series of 10 2-fold dilutions on C1:C11 96 well microplate `calibration plate`. Start with C1 and end with a final excess volume of 100.0 microliter in C11.  For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
28. Perform a series of 10 2-fold dilutions on D1:D11 96 well microplate `calibration plate`. Start with D1 and end with a final excess volume of 100.0 microliter in D11.  For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
29. Perform a series of 10 2-fold dilutions on E1:E11 96 well microplate `calibration plate`. Start with E1 and end with a final excess volume of 100.0 microliter in E11.  For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
30. Perform a series of 10 2-fold dilutions on F1:F11 96 well microplate `calibration plate`. Start with F1 and end with a final excess volume of 100.0 microliter in F11.  For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
31. Perform a series of 10 2-fold dilutions on G1:G11 96 well microplate `calibration plate`. Start with G1 and end with a final excess volume of 100.0 microliter in G11.  For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
32. Perform a series of 10 2-fold dilutions on H1:H11 96 well microplate `calibration plate`. Start with H1 and end with a final excess volume of 100.0 microliter in H11.  For each 100.0 microliter transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
33. Transfer 100.0 microliter of `calibration plate` sample to  waste container `discard`.  This step ensures that all wells contain an equivalent volume. Be sure to change pipette tips for every well to avoid cross-contamination.
34. Transfer 100.0 microliter of `PBS` sample to wells A1:D12 of 96 well microplate `calibration plate`.  This will bring all wells to volume 200 microliter.
35. Transfer 100.0 microliter of `molecular grade H2O` sample to wells E1:H12 of 96 well microplate `calibration plate`.  This will bring all wells to volume 200 microliter.
36. Measure fluorescein and bead fluorescence of `calibration plate` with excitation wavelength of 488.0 nanometer and emission filter of 530.0 nanometer and 30.0 nanometer bandpass.
37. Measure absorbance of `calibration plate` at 600.0 nanometer.
38. Import data into the provided Excel file: Dataset: [singlecolor-particle-calibration.xlsx](singlecolor-particle-calibration.xlsx).

---
Timestamp: 2023-06-08 23:41:20.743422
Protocol version: v1.0a2-221-gafe71b3

