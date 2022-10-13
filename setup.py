from setuptools import setup

test_deps = ["nbmake", "pytest-xdist", "pre-commit", "nbstripout"]
notebook_deps = ["ipython", "ipywidgets"]
extras = {
    "test": test_deps,
    "notebook": notebook_deps
}

setup(name='paml',
      description='Protocol Activity Modeling Language',
      version='1.0a1',
      install_requires=[
            'sbol3',
            'sparqlwrapper',
            'python-dateutil',
            'sbol-factory',
            'requests',
            'graphviz',
            'tyto',
            'numpy',
            'openpyxl',
            'autoprotocol',
            'transcriptic',
            'requests_html',
            "container-ontology @ https://github.com/rpgoldman/container-ontology/tarball/main",
            "xarray",
      ],
      tests_require=test_deps,
      extras_require=extras,
      packages=['paml', 'paml_convert', 'paml_convert.autoprotocol', 'paml_convert.markdown', 'paml_convert.opentrons', 'paml.lib', 'paml_time', 'uml', 'examples', 'owl_rdf_utils'],
      package_data={'paml': ['paml.ttl', 'lib/*.ttl'],
                    'paml_convert': ['markdown/template.xlsx'],
                    'uml': ['uml.ttl'],
                    'paml_time': ['paml_time.ttl']},

      include_package_data=True
)
