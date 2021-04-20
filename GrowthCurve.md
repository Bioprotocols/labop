# SD2 Yeast growth curve protocol

## Description:

Protocol from SD2 Yeast States working group for studying growth curves:
Grow up cells and read with plate reader at n-hour intervals



## Protocol Inputs:
* Protocol input: strain_plate: Plate of strains to grow


## Materials
* [Synthetic Complete Media](file:///Users/jakebeal/projects/SD2/PAML/test/testfiles/TBD)
* [Phosphate-Buffered Saline](https://identifiers.org/pubchem.substance:24978514)
* [Synthetic Complete Media plus 40nM Doxycycline](file:///Users/jakebeal/projects/SD2/PAML/test/testfiles/TBD)


## Containers
* [PBS Source](https://identifiers.org/ncit:C43169) ([Bottle](https://identifiers.org/ncit:C43169))
* [Growth Curve Plate](https://identifiers.org/ncit:C43377) ([Microplate](https://identifiers.org/ncit:C43377))
* [Overnight SC Media Source](https://identifiers.org/ncit:C43169) ([Bottle](https://identifiers.org/ncit:C43169))
* [Overnight Growth Plate](https://identifiers.org/ncit:C43377) ([Microplate](https://identifiers.org/ncit:C43377))
* [SC Media + 40nM Doxycycline Source](https://identifiers.org/ncit:C43169) ([Bottle](https://identifiers.org/ncit:C43169))


## Steps
1. Pipette 117200.0 microliter of [Synthetic Complete Media plus 40nM Doxycycline](file:///Users/jakebeal/projects/SD2/PAML/test/testfiles/TBD) into [SC Media + 40nM Doxycycline Source](https://identifiers.org/ncit:C43169)

2. Pipette 117760.0 microliter of [Phosphate-Buffered Saline](https://identifiers.org/pubchem.substance:24978514) into [PBS Source](https://identifiers.org/ncit:C43169)

3. Pipette 98.0 milliliter of [Synthetic Complete Media](file:///Users/jakebeal/projects/SD2/PAML/test/testfiles/TBD) into [Overnight SC Media Source](https://identifiers.org/ncit:C43169)

4. Pipette 700.0 microliter of [Synthetic Complete Media plus 40nM Doxycycline](file:///Users/jakebeal/projects/SD2/PAML/test/testfiles/TBD) from [SC Media + 40nM Doxycycline Source](https://identifiers.org/ncit:C43169) into [Growth Curve Plate](https://identifiers.org/ncit:C43377)

5. Remove seal from strain_plate

6. Pipette 500.0 microliter of [Synthetic Complete Media](file:///Users/jakebeal/projects/SD2/PAML/test/testfiles/TBD) from [Overnight SC Media Source](https://identifiers.org/ncit:C43169) into [Overnight Growth Plate](https://identifiers.org/ncit:C43377)

7. Pipette 5.0 microliter from strain_plate into [Overnight Growth Plate](https://identifiers.org/ncit:C43377), mixing by pipetting up and down 10.0  times at destination

8. Seal strain_plate with breathable seal

9. Seal [Overnight Growth Plate](https://identifiers.org/ncit:C43377) with breathable seal

10. Incubate [Overnight Growth Plate](https://identifiers.org/ncit:C43377) for 16.0 hour at temperature 30.0 degree Celsius, shaking at 350.0 rpm

11. Remove seal from [Overnight Growth Plate](https://identifiers.org/ncit:C43377)

12. Run protocol "Split samples and measure, without dilution" with inputs: [Overnight Growth Plate](https://identifiers.org/ncit:C43377) for Samples to measure
13. Pipette 2.0 microliter from [Overnight Growth Plate](https://identifiers.org/ncit:C43377) into [Growth Curve Plate](https://identifiers.org/ncit:C43377), mixing by pipetting up and down 10.0  times at destination

14. Incubate [Growth Curve Plate](https://identifiers.org/ncit:C43377) for 1.0 hour at temperature 30.0 degree Celsius, shaking at 350.0 rpm

15. Seal [Overnight Growth Plate](https://identifiers.org/ncit:C43377) with breathable seal

16. Run protocol "Split samples, dilute, and measure" with inputs: [Growth Curve Plate](https://identifiers.org/ncit:C43377) for Samples to measure and [PBS Source](https://identifiers.org/ncit:C43169) for Source for PBS
17. Incubate [Growth Curve Plate](https://identifiers.org/ncit:C43377) for 2.0 hour at temperature 30.0 degree Celsius, shaking at 350.0 rpm

18. Run protocol "Split samples, dilute, and measure" with inputs: [Growth Curve Plate](https://identifiers.org/ncit:C43377) for Samples to measure and [PBS Source](https://identifiers.org/ncit:C43169) for Source for PBS
19. Incubate [Growth Curve Plate](https://identifiers.org/ncit:C43377) for 3.0 hour at temperature 30.0 degree Celsius, shaking at 350.0 rpm

20. Run protocol "Split samples, dilute, and measure" with inputs: [Growth Curve Plate](https://identifiers.org/ncit:C43377) for Samples to measure and [PBS Source](https://identifiers.org/ncit:C43169) for Source for PBS
21. Incubate [Growth Curve Plate](https://identifiers.org/ncit:C43377) for 3.0 hour at temperature 30.0 degree Celsius, shaking at 350.0 rpm

22. Run protocol "Split samples, dilute, and measure" with inputs: [Growth Curve Plate](https://identifiers.org/ncit:C43377) for Samples to measure and [PBS Source](https://identifiers.org/ncit:C43169) for Source for PBS
23. Incubate [Growth Curve Plate](https://identifiers.org/ncit:C43377) for 9.0 hour at temperature 30.0 degree Celsius, shaking at 350.0 rpm

24. Run protocol "Split samples, dilute, and measure" with inputs: [Growth Curve Plate](https://identifiers.org/ncit:C43377) for Samples to measure and [PBS Source](https://identifiers.org/ncit:C43169) for Source for PBS
25. Incubate [Growth Curve Plate](https://identifiers.org/ncit:C43377) for 3.0 hour at temperature 30.0 degree Celsius, shaking at 350.0 rpm

26. Run protocol "Split samples, dilute, and measure" with inputs: [Growth Curve Plate](https://identifiers.org/ncit:C43377) for Samples to measure and [PBS Source](https://identifiers.org/ncit:C43169) for Source for PBS
27. Incubate [Growth Curve Plate](https://identifiers.org/ncit:C43377) for 3.0 hour at temperature 30.0 degree Celsius, shaking at 350.0 rpm

28. Run protocol "Split samples, dilute, and measure" with inputs: [Growth Curve Plate](https://identifiers.org/ncit:C43377) for Samples to measure and [PBS Source](https://identifiers.org/ncit:C43169) for Source for PBS
