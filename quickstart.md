---
layout: default
title: "Quickstart"
permalink: /quickstart/
---

There are two main options to getting started with LabOP:
- [pyLabOP](https://github.com/Bioprotocols/labop): the LabOP Python library.
- [PAMLED](https://github.com/Bioprotocols/laboped): the LabOP Editor web application.

# pyLabOP

1. Install pyLabOP from PyPI, in your Python environment:
```bash
pip3 install pylabop
```
or install from source:
```bash
git clone https://github.com/Bioprotocols/labop
pip3 install labop
```

2. LabOP visualizations currently depend on the graphviz application. To install graphviz, run (per https://github.com/ts-graphviz/setup-graphviz):
- Mac: brew install graphviz
- Linux: apt-get install graphviz libgraphviz-dev pkg-config
- Windows: choco install graphviz

3. To use LabOP in your client application, import the LabOP, UML, and SBOL3 modules:
```bash
import labop, uml, sbol3
```

4. Initialize an SBOL document to hold the protocol and referenced objects:
```bash
sbol3.set_namespace('http://example.org/synbio/')
doc = sbol3.Document()
```
and (optionally) read a previously saved document:
```bash
doc.read('test/testfiles/igem_ludox_test.nt')
```

# Create a Simple Protocol

1. Define a protocol object:
```bash
protocol = labop.Protocol('MyNewProtocol')
doc.add(protocol)
```

2. Import a primitive library:
```bash
labop.import_library('sample_arrays')
```

3. Create a primitive activity:
```bash
plate = protocol.primitive_step('EmptyContainer', specification="MyPlate")
```

4. Visualize the protocol with GraphViz:
```bash
protocol.to_dot().view()
```
