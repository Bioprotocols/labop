from setuptools import setup

setup(name='paml',
      description='Protocol Activity Modeling Language',
      version='1.0a1',
      install_requires=[
            'sbol3',
            'sbol-factory==1.0a6',
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
