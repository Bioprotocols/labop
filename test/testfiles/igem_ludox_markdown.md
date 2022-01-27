# iGEM 2018 LUDOX OD calibration protocol

## Description:

With this protocol you will use LUDOX CL-X (a 45% colloidal silica suspension) as a single point reference to
obtain a conversion factor to transform absorbance (OD600) data from your plate reader into a comparable
OD600 measurement as would be obtained in a spectrophotometer. This conversion is necessary because plate
reader measurements of absorbance are volume dependent; the depth of the fluid in the well defines the path
length of the light passing through the sample, which can vary slightly from well to well. In a standard
spectrophotometer, the path length is fixed and is defined by the width of the cuvette, which is constant.
Therefore this conversion calculation can transform OD600 measurements from a plate reader (i.e. absorbance
at 600 nm, the basic output of most instruments) into comparable OD600 measurements. The LUDOX solution
is only weakly scattering and so will give a low absorbance value.
        


## Protocol Materials:
* [LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O](https://identifiers.org/pubchem.substance:24866361)
* [Water, sterile-filtered, BioReagent, suitable for cell culture](https://identifiers.org/pubchem.substance:24901740)


## Protocol Inputs:
* `wavelength` = 100.0 nanometer

## Protocol Outputs:
* `absorbance`

## Steps
1. Provision a container named `samples` meeting specification: cont:ClearPlate and 
 cont:SLAS-4-2004 and
 (cont:wellVolume some 
    ((om:hasUnit value om:microlitre) and
     (om:hasNumericalValue only xsd:decimal[>= "200"^^xsd:decimal]))).
2. Pipette 100.0 microliter of [Water, sterile-filtered, BioReagent, suitable for cell culture](https://identifiers.org/pubchem.substance:24901740) into `samples(A1:D1)`.
3. Pipette 100.0 microliter of [LUDOX(R) CL-X colloidal silica, 45 wt. % suspension in H2O](https://identifiers.org/pubchem.substance:24866361) into `samples(A2:D2)`.
4. Make absorbance measurements (named `measurements`) of `samples(A1:D2)` at 100.0 nanometer.
5. Report values for `absorbance` from `measurements`.
