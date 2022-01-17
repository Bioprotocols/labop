# PAML
Protocol Activity Modeling Language (PAML) is a representation designed to simplify the exchange of protocols between laboratories. This project includes both an ontology describing PAML and a python library to manipulate PAML documents, which are stored as RDF.  The PAML specification is in [the PAML-specification repository](https://github.com/Bioprotocols/PAML-specification).

# Installation

Clone the repository and then, in its root directory, run:
```
pip3 install .
```

If one does not wish to check out the repository, the following will also work:

```
pip3 install git+https://github.com/Bioprotocols/paml.git
```

# API

To use PAML in your client application, go to the root directory of the project repository:
```
import paml
```
The API follows the same conventions as [OPIL](https://github.com/sd2e/opil).

# Example Notebooks

See [notebooks](https://github.com/Bioprotocols/paml/tree/main/notebooks) for examples of how to use PAML.  An [interactive version](https://colab.research.google.com/drive/1WPvQ0REjHMEsginxXMj1ewqfFHZqSyM8?usp=sharing) of the main demonstration notebook [notebooks/paml_demo.ipynb](https://github.com/Bioprotocols/paml/tree/main/notebooks/paml_demo.ipynb) is also hosted on Google Collab.   The interactive version is shared as view only, but you can make a copy to modify with `File -> Save a copy in Drive` by saving it on your own Google Drive account.

# Strateos Integration
The `secrets` directory includes a template to configure Strateos credentials.  It requires renaming and editing the provided sample. (Please, never commit or share actual credentials!)
```
cp secrets/strateos_secrets.json.sample secrets/strateos_secrets.json
# Edit contents of secrets/strateos_secrets.json
```
The secrets for the Strateos API are used by the notebook `notebooks/Autoprotocol.ipynb` and pytest `test/test_convert.py`.  Additional user permissions may be required to submit runs to Strateos.  Please contact [Strateos support](https://strateos.com/contact-us/) for assistance.
