# PAML
Protocol Activity Modeling Language (PAML) is a representation designed to simplify the exchange of protocols between laboratories. This project includes both an ontology describing PAML and a python library to 

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

# Strateos Integration
The `secrets` directory includes a template to configure Strateos credentials.  It requires renaming and editing the provided sample. (Please, never commit or share actual credentials!)
```
cp secrets/strateos_secrets.json.sample secrets/strateos_secrets.json
# Edit contents of secrets/strateos_secrets.json
```
The secrets for the Strateos API are used by the notebook `notebooks/Autoprotocol.ipynb` and pytest `test/test_convert.py`.  Additional user permissions may be required to submit runs to Strateos.  Please contact [Strateos support](https://strateos.com/contact-us/) for assistance.
