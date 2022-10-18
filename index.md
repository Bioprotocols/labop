---
layout: default
title: LabOP
permalink: /
---
# The Laboratory Open Protocol Language (LabOP)

## What is LabOP?

LabOP is an *open* specification for laboratory protocols, that solves common interchange problems stemming from variations in scale, labware, instruments, and automation. LabOP was built from the ground-up to support protocol interchange.  It provides an extensible library of protocol primitives that capture the control and data flow needed for simple calibration and culturing protocols to industrial control.

## Software Ecosystem

LabOP's rich representation underpins an ecosystem of several powerful software tools, including:

- [labop](https://www.github.com/bioprotocols/labop): the Python LabOP library, which supports:
  - *Programming* LabOP protocols in Python,
  - *Serialization* of LabOP protocols conforming to the LabOP RDF specification,
  - *Execution* in the native LabOP semantics (rooted in the UML activity model),
  - *Specialization* of protocols to 3rd-party protocol formats (including Autoprotocol, OpenTrons, and human readible formats), and
  - *Integration* with instruments (including OpenTrons OT2, Echo, and SiLA-based automation).
- [pamled](https://www.github.com/bioprotocols/pamled): the web-based LabOP Editor, which supports:
  - *Programming* LabOP protocols quickly with low-code visual scripts,
  - *Storing* protocols on the cloud,
  - *Exporting* protocol specializations for use in other execution frameworks,

## [About the Bioprotocols Working Group](about.md)
