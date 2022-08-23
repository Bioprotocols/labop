---
layout: default
title: "Quickstart"
permalink: /quickstart/
---

There are two main options to getting started with PAML:
- [pyPAML](https://github.com/Bioprotocols/paml): the PAML Python library.
- [PAMLED](https://github.com/Bioprotocols/pamled): the PAML Editor web application.

# pyPAML

1. Install pyPAML from PyPI, in your Python environment:
```bash
pip3 install pypaml
```
or install from source:
```bash
git clone https://github.com/Bioprotocols/paml
pip3 install paml
```

2. PAML visualizations currently depend on the graphviz application. To install graphviz, run (per https://github.com/ts-graphviz/setup-graphviz):
- Mac: brew install graphviz
- Linux: apt-get install graphviz libgraphviz-dev pkg-config
- Windows: choco install graphviz

3. To use PAML in your client application, import the PAML, UML, and SBOL3 modules:
```bash
import paml, uml, sbol3
```

4. Initialize an SBOL document to hold the protocol and referenced objects:
```bash
doc = sbol3.Document()
```
and (optionally) read a previously saved document:
```bash
doc.read('test/testfiles/igem_ludox_test.nt')
```
