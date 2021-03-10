from setuptools import setup

# This version includes a patch that squelches logging in
# the opil factory, which was conflicting with logging in
# other modules

setup(name='paml',
      description='Protocol Activity Modeling Language',
      version='1.0a1',
      install_requires=[
            'sbol3==1.0a7',
            'rdflib>=5.0.0',
            'rdflib-jsonld>=0.5.0',
            'sparqlwrapper>=1.8.5',
            'pyshacl>=0.13.3',
            'python-dateutil>=2.8.1',
            'sbol_factory==1.0a1',
            'requests',
            'graphviz'
      ],
      packages=['paml'],
      package_data={'paml': ['paml.ttl']},
      include_package_data=True,
#      entry_points = {
#            'rdf.plugins.sparqleval': [
#            'custom_eval =  custom_eval:customEval',
#        ],
#      }
)
