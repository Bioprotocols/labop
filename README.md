# LabOP
Laboratory Open Procotol Language (LabOP) is a representation designed to simplify the exchange of protocols between laboratories. This project includes both an ontology describing LabOP and a python library to manipulate LabOP documents, which are stored as RDF.  The LabOP specification is in [the LabOP-specification repository](https://github.com/Bioprotocols/LabOP-specification).

# Installation

The LabOP package is available by PyPI:

```
pip3 install labop
```

The LabOP repo also includes git submodules containing the optional utility `labop-check` for checking consistency of protocol representations and a demo version of the `container-ontology` which provides standardized descriptions for laboratory containers.  These are currently not available as packages.  If you wish to use these you will have to clone the LabOP repo and install each of these separately:

```
git clone https://github.com/Bioprotocols/labop
pip3 install .
cd labop/labop-check
pip3 install .
cd ../container-ontology
pip3 install .
```

LabOP visualizations currently depend on the `graphviz` application. To install graphviz, run (per https://github.com/ts-graphviz/setup-graphviz):
* Mac: `brew install graphviz`
* Linux: `apt-get install graphviz libgraphviz-dev pkg-config`
* Windows: `choco install graphviz`

# API

To use LabOP in your client application, import the LabOP, UML, and SBOL3 modules:

```python
import labop, uml, sbol3
```

The LabOP data model is encoded as an ontology using the Web Ontology Language (OWL). (A Turtle serialization of the LabOP ontology can be found in the `labop` directory, and uses the UML ontology found in the `uml` directory.) The module's API is dynamically generated directly from this OWL specification immediately upon import of the module into the user's Python environment. The ontology specifies the Python classes, their attributes, their types, and their cardinality.

## Working with LabOP Documents

All file I/O is handled through an SBOL `Document` object. In the following example, we read a file that describes the protocol for an OD calibration using water and LUDOX. The file format can be any RDF format:

```python
doc = sbol3.Document()
doc.read('test/testfiles/igem_ludox_test.nt')
```

Once a `Document` is loaded, you can inspect and manipulate its contents. For example, the following prints an inventory of objects and their metadata:

```python
for obj in doc.objects:
    print(obj.identity)
    print(obj.name)
    print(obj.description)
    print()
```

The `name` attribute is used for human-readable and/or lab-specific identifiers. The `identity` attribute specifies the unique Uniform Resource Identifier (URI) for each object. The URI can be used to retrieve specific objects from the Document.

```python
ludox = doc.find('https://bbn.com/scratch/LUDOX')
```

## Creating objects

Every LabOP object is identified by a unique URI. Objects come in two types, "top-level" objects that can stand alone, such as a `Protocol` or a `Primitive`, and "child" objects that only make sense within the context of their top-level object, such as a protocol step (`ActivityNode`) or a `Parameter`.

When a new "top-level" object is created, the full URI can be either prodiced or automatically generated from a local identifier. Every constructor for a top-level LabOP object takes a local ID or URI as its first argument. If given a local ID, the full URI is then generated from a namespace and the local ID. This local ID must consist of only alphanumeric characters and/or underscores.

When constructing a new `Document`, the general workflow is as follows. First, set the namespace that governs new objects. Second, create new objects. Finally, add the new object to the `Document`.  For example:

```python
sbol3.set_namespace('http://example.org/synbio/')
doc = sbol3.Document()
protocol = labop.Protocol('TimeSeries')
doc.add(protocol)
doc.find('http://example.org/synbio/TimeSeries')
```

Child objects are not named by the user, but receive their names automatically when added to a parent. For example:

```python
step = uml.CallBehaviorAction()
protocol.nodes += [step]
step.identity  # http://example.org/synbio/TimeSeries/CallBehaviorAction1
```

Note that in many cases, it is better to create child objects by means of helper functions:

```python
labop.import_library('sample_arrays')
four_wells = protocol.primitive_step('PlateCoordinates', coordinates='A2:D2')  # Note: still needs source plate indicated
```

## Validation

A `Document` can be validated as follows:

```python
for issue in doc.validate():
    print(issue)
```

# Protocol Execution

A `Protocol` may be executed an arbitrary amount of times, resulting in a unique history each time that captured by an `Execution`.  Such `Executions` may record actual times or feedback measurements from instruments during execution.

The `ExecutionEngine` class is used to carry out a protocol. An `ExecutionEngine` interprets a `Protocol` in an application-specific manner using a `BehaviorSpecialization` object.  For example, a `BehaviorSpecialization` might translate a protocol encoded in LabOP into specific instructions that a particular laboratory's instrumentation or robotics can interpret.  Converter tools can also be implemented.  Currently the LabOP project includes a Markdown converter that will convert a LabOP-encoded protocol into a human-readable Markdown document. If no `BehaviorSpecialization` is provided, the default will be used, which is essentially a no-op, but provides some utility for testing and development.

Each protocol execution requires an `Agent`, used to record the person, laboratory, or machine executing the protocol.  An execution may also require input `ParameterValues` to configure the protocol.

Following is an example execution that converts a protocol for optical density measurement into Markdown format to the `example.md` file:

```python
agent = sbol3.Agent("2022_Hogwart_iGEM_team")  # Used to describe the person or machine executing the protocol
ee = ExecutionEngine(specializations=[MarkdownSpecialization("example.md")])
parameter_values = [
    labop.ParameterValue(parameter=protocol.get_input("wavelength"),
                        value=sbol3.Measure(600, tyto.OM.nanometer))
]
execution = ee.execute(protocol, agent, id="OD_measurement", parameter_values=parameter_values)
```

# Example Notebooks

See [notebooks](https://github.com/Bioprotocols/labop/tree/main/notebooks) for examples of how to use LabOP.  An [interactive version](https://colab.research.google.com/drive/1WPvQ0REjHMEsginxXMj1ewqfFHZqSyM8?usp=sharing) of the main demonstration notebook [notebooks/labop_demo.ipynb](https://github.com/Bioprotocols/labop/tree/main/notebooks/labop_demo.ipynb) is also hosted on Google Collab.   The interactive version is shared as view only, but you can make a copy to modify with `File -> Save a copy in Drive` by saving it on your own Google Drive account.

# Strateos Integration
The `secrets` directory includes a template to configure Strateos credentials.  It requires renaming and editing the provided sample. (Please, never commit or share actual credentials!)
```
cp secrets/strateos_secrets.json.sample secrets/strateos_secrets.json
# Edit contents of secrets/strateos_secrets.json
```
The secrets for the Strateos API are used by the notebook `notebooks/Autoprotocol.ipynb` and pytest `test/test_convert.py`.  Additional user permissions may be required to submit runs to Strateos.  Please contact [Strateos support](https://strateos.com/contact-us/) for assistance.

# Generating the LabOP Specification Document

The LabOP documentation can be generated from its RDF specification (e.g., `labop.ttl`).  The generated latex resides in a direcory parallel to the labop source.  If you are in `./labop`, then running the command below will generate latex in `../labop-specification`.  The labop-specification directory corresponds to the cloned project [https://github.com/Bioprotocols/labop-specification](https://github.com/Bioprotocols/labop-specification).  The labop-specification also includes several static files used to compile the documentation. The documentation consisting of LaTeX and PDF Documents that describe the LabOP protocol representation can be generated by running the following script in `./labop`:

```
python3 doc/generate_specification_content.py
cd ../labop-specification
pdflatex labop
bibtex labop
pdflatex labop
```
