# paml
Protocol Activity Modeling Language

# Installation

```
pip3 install paml
```

# API

To use PAML in your client application, go to the root directory of the project repository:
```
import paml
```
The API follows the same conventions as [OPIL](https://github.com/sd2e/opil).

# Building documentation

Running the following at the commandline will generate UML diagrams for the PAML data model.
```
python3 -c "from paml import __umlfactory__; __umlfactory__.generate('uml')"
```

# Visualizing Documents

A commandline script is included to aid in visualizing a Document tree:
```
python3 graph_paml.py -i lib/liquid_handling.ttl
```

