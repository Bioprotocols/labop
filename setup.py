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
            'sbol-factory==1.0a6',
            'requests',
            'graphviz',
            'tyto',
            'numpy',
            'openpyxl'
      ],
      packages=['paml', 'paml_convert', 'paml.lib', 'paml_time', 'uml'],
      package_data={'paml': ['paml.ttl', 'lib/*.ttl'],
                    'paml_convert': ['markdown/template.xlsx'],
                    'uml': ['uml.ttl'],
                    'paml_time': ['paml_time.ttl']},
      include_package_data=True,
)
