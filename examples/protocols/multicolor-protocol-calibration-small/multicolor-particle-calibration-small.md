# Multicolor fluorescence per bacterial particle calibration

Plate readers report fluorescence values in arbitrary units that vary widely from instrument to instrument. Therefore absolute fluorescence values cannot be directly compared from one instrument to another. In order to compare fluorescence output of biological devices, it is necessary to create a standard fluorescence curve. This variant of the protocol uses two replicates of three colors of dye, plus beads.
Adapted from [https://dx.doi.org/10.17504/protocols.io.bht7j6rn](https://dx.doi.org/10.17504/protocols.io.bht7j6r) and [https://dx.doi.org/10.17504/protocols.io.6zrhf56](https://dx.doi.org/10.17504/protocols.io.6zrhf56)


## Protocol Outputs:
* Dataset: [multicolor-particle-calibration-small.xlsx](multicolor-particle-calibration-small.xlsx)


## Protocol Materials:
* [Water, sterile-filtered, BioReagent, suitable for cell culture](https://identifiers.org/pubchem.substance:24901740)
* [NanoCym 950 nm monodisperse silica nanoparticles](https://nanocym.com/wp-content/uploads/2018/07/NanoCym-All-Datasheets-.pdf)
* [Phosphate Buffered Saline](https://pubchem.ncbi.nlm.nih.gov/substance/329753341)
* [Fluorescein](https://pubchem.ncbi.nlm.nih.gov/substance/329753341)
* [Cascade Blue](https://pubchem.ncbi.nlm.nih.gov/substance/329753341)
* [Sulforhodamine](https://pubchem.ncbi.nlm.nih.gov/substance/329753341)
* stock reagent container (x 2)
* 96 well microplate


## Protocol Steps:
1. Provision the stock reagent container containing `Fluorescein calibrant`.
2. Provision the stock reagent container containing `PBS`.
3. Pipette 5000.0uL of [Phosphate Buffered Saline](https://pubchem.ncbi.nlm.nih.gov/substance/329753341) into `PBS`.
4. Pipette 500.0uL of [Fluorescein](https://pubchem.ncbi.nlm.nih.gov/substance/329753341) into `Fluorescein calibrant`.
5. Transfer 1.0mL of `PBS` sample to  stock reagent container `Fluorescein calibrant`. The reconstituted `Fluorescein` should have a final concentration of 10 uM in `Phosphate Buffered Saline`.
6. Provision a container named `calibration plate` such as: 
	[Corning96WellPlate360uLFlat](https://sift.net/container-ontology/container-ontology#Corning96WellPlate360uLFlat).
7. Transfer 200.0uL of `Fluorescein calibrant` sample to wells A1 of 96 well microplate `calibration plate`.
8. Transfer 100.0uL of `PBS` sample to wells A2:D12 of 96 well microplate `calibration plate`.
9. Perform a series of 10 2-fold dilutions on wells A1:A11 of 96 well microplate `calibration plate`. Start with A1 and end with a final volume of 200.0uL in A11.  For each 100.0uL transfer, pipette up and down 3X to ensure the dilution is mixed homogeneously.
10. Measure fluorescein and bead fluorescence of `calibration plate` with excitation wavelength of 488.0nm and emission filter of 530.0nm and 30.0nm bandpass.
11. Import data into the provided Excel file: Dataset: [multicolor-particle-calibration-small.xlsx](multicolor-particle-calibration-small.xlsx).

---
Timestamp: 2023-05-11 15:31:36.160034
Protocol version: 1.1b
