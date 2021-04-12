from setuptools import setup

setup(name='paml',
      description='Protocol Activity Modeling Language',
      version='1.0a1',
      install_requires=[
            'sbol3==1.0a8',
            'rdflib>=5.0.0',
            'rdflib-jsonld>=0.5.0',
            'sparqlwrapper>=1.8.5',
            'pyshacl>=0.13.3',
            'python-dateutil>=2.8.1',
            'sbol-factory==1.0a2.post0',
            'requests',
            'graphviz', 'tyto'
      ],
      packages=['paml'],
      package_data={'paml': ['paml.ttl', 'lib/*.ttl']},
      include_package_data=True,
)
