from setuptools import setup

setup(name='paml',
      description='Protocol Activity Modeling Language',
      version='1.0a1',
      install_requires=[
            'sbol3',
            'rdflib>=5.0.0, <6.0.0',
            'rdflib-jsonld>=0.5.0',
            'sparqlwrapper>=1.8.5',
            'pyshacl>=0.13.3',
            'python-dateutil>=2.8.1',
            'sbol-factory',
            'requests',
            'graphviz',
            'tyto',
            'numpy',
            'openpyxl'
      ],
      packages=['paml', 'paml_md', 'paml.lib', 'uml'],
      package_data={'paml': ['paml.ttl', 'lib/*.ttl'],
                    'paml_md': ['template.xlsx'],
                    'uml': ['uml.ttl']},
      include_package_data=True,
)
