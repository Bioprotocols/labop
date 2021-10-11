import glob

from sbol_factory import UMLFactory
import os
from shutil import copy
from pathlib import Path

print('Warning: this script is fragile and assumes that PAML and PAML-specification are sibling directories on Mac or Unix.')

print('Loading UML')
uml_module = UMLFactory(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../uml/uml.ttl'), 'http://bioprotocols.org/uml#')
print('Generating UML specification materials')
uml_module.generate('uml_classes')

print('Moving UML to specification folder')
copy('umlDataModel.tex', '../PAML-specification/umlDataModel.tex')
os.remove('umlDataModel.tex')
Path('../PAML-specification/uml_classes/').mkdir(parents=True, exist_ok=True)
for file in glob.glob('uml_classes/*'):
    copy(file, '../PAML-specification/uml_classes/')
    os.remove(file)

print('Loading PAML')
paml_module = UMLFactory(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../paml/paml.ttl'),
           'http://bioprotocols.org/paml#')
print('Generating PAML specification materials')
paml_module.generate('paml_classes')

print('Moving PAML to specification folder')
copy('pamlDataModel.tex', '../PAML-specification/pamlDataModel.tex')
os.remove('pamlDataModel.tex')
Path('../PAML-specification/paml_classes/').mkdir(parents=True, exist_ok=True)
for file in glob.glob('paml_classes/*'):
    copy(file, '../PAML-specification/paml_classes/')
    os.remove(file)
print('Update complete')
