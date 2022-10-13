# The Protocol Activity Modeling Language (PAML)

## What is PAML?

PAML is an *open* specification for laboratory protocols, that solves common interchange problems stemming from variations in scale, labware, instruments, and automation. PAML was built from the ground-up to support protocol interchange.  It provides an extensible library of protocol primitives that capture the control and data flow needed for simple calibration and culturing protocols to industrial control.  

## Software Ecosystem

PAML's rich representation underpins an ecosystem of several powerful software tools, including:

- [pypaml](https://www.github.com/bioprotocols/paml): the Python PAML library, which supports:
  - *Programming* PAML protocols in Python,
  - *Serialization* of PAML protocols conforming to the PAML RDF specification,
  - *Execution* in the native PAML semantics (rooted in the UML activity model),
  - *Specialization* of protocols to 3rd-party protocol formats (including Autoprotocol, OpenTrons, and human readible formats), and
  - *Integration* with instruments (including OpenTrons OT2, Echo, and SiLA-based automation).
- [pamled](https://www.github.com/bioprotocols/paml): the web-based PAML Editor, which supports:
  - *Programming* PAML protocols quickly with low-code visual scripts,
  - *Storing* protocols on the cloud,
  - *Exporting* protocol specializations for use in other execution frameworks,
  
## [About the Bioprotocols Working Group](about.md)
