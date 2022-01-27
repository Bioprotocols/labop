from setuptools import setup
import sys
import os
import subprocess

test_deps = [
    'nbmake',
    'pytest-xdist',
    'owl_rdf_utils'
]
extras = {
    'test': test_deps,
}

setup(name='pypaml',
      description='Protocol Activity Modeling Language',
      version='1.0a1',
      license='MIT',
      license_files=('LICENSE.txt'),
      install_requires=[
            'sbol3>=1.0b6',
            'sparqlwrapper>=1.8.5',
            'python-dateutil>=2.8.1',
            'sbol-factory==1.0a8',
            'requests',
            'graphviz',
            'tyto',
            'numpy',
            'openpyxl',
            'autoprotocol',
            'transcriptic',
            'requests_html',
            "ipython",
            "pre-commit",
            "ipywidgets",
      ],
      tests_require=test_deps,
      extras_require=extras,
      packages=['paml', 'paml_convert', 'paml_convert.autoprotocol', 'paml_convert.markdown', 'paml.lib', 'paml_time', 'uml'],
      package_data={'paml': ['paml.ttl', 'lib/*.ttl'],
                    'paml_convert': ['markdown/template.xlsx'],
                    'uml': ['uml.ttl'],
                    'paml_time': ['paml_time.ttl']},
      scripts=['scripts/to_sorted_ntriples', 'scripts/restrictions'],
      include_package_data=True,
)
