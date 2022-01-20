import setuptools
import sys
import os
import subprocess
from setuptools.command.install import install

def pip_install(url):
    subprocess.check_output([sys.executable, '-m', 'pip', 'install', url])

#pip_install("git+https://github.com/rpgoldman/container-ontology.git")

test_deps = [
    'nbmake',
    'pytest-xdist'
]
extras = {
    'test': test_deps,
}

# This is a wrapper around setuptools.setup that performs installation on 
# the git submodule for the container-ontology
#
# It may be removed later when the container-ontology is deployed on PyPI.
# See https://github.com/rpgoldman/container-ontology/issues/13
class PostInstall(install):
    def run(self):
        setuptools.setup(**args)
        subprocess.run(['python3', os.path.join('container-ontology', 'setup.py')])

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

      include_package_data=True,
      cmdclass={'install': PostInstall, },
)
