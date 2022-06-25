# HARMONY 2022 Example Cell Calibration protocol

## Description:
With this protocol you will prepare a standard curve using a fluorescein calibrant and measure the fluorescence of a genetic circuit expressing GFP.


## Protocol Materials:
* [Fluoroscein](https://identifiers.org/pubchem.substance:329753341)
* [lb_broth](https://identifiers.org/pubchem.substance:441068474)
* [water](https://identifiers.org/pubchem.substance:24901740)
* [Test_circuit](https://identifiers.org/SBO:0000251)
* [E. coli DH5alpha](https://identifiers.org/taxonomy:668369)


## Protocol Inputs:
* `emissionWavelength` = 485.0* `excitationWavelength` = 510.0

## Protocol Outputs:


## Steps
1. Provision a container named `plate 1` meeting specification: cont:Well96Plate.
2. Transform `Test_circuit` DNA into `E. coli DH5alpha` and plate transformants on lb_broth.
3. Pipette 200.0 microliter of [lb_broth](https://identifiers.org/pubchem.substance:441068474) into `plate 1(['A12', 'B12', 'C12', 'D12', 'E12', 'F12', 'G12', 'H12'])`.
4. Pipette 200.0 microliter of [lb_broth](https://identifiers.org/pubchem.substance:441068474) into `plate 1(['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2'])`.
5. Perform a series of 8 2-fold dilutions on `Fluoroscein` using `water` as diluent to a final volume of 200.0 microliter in wells A1, B1, C1, D1, E1, F1, G1, H1 of Well96Plate `plate 1`.
6. Inoculate E. coli DH5alpha+Test_circuit transformant in wells A2, B2, C2, D2, E2, F2, G2, H2 of plate 1 Well96Plate
7. Incubate `plate 1` for 6.0 hour at 37.0 degree Celsius .
8. Report values for .
