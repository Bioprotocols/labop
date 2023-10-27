from setuptools import setup

test_deps = ["nbmake", "pytest-xdist", "pre-commit", "nbstripout"]
notebook_deps = ["ipython", "ipywidgets"]
autoprotocol_deps = ["autoprotocol", "transcriptic"]
extras = {
    "test": test_deps,
    "notebook": notebook_deps,
    "autoprotocol": autoprotocol_deps,
}
setup(
    name="labop",
    description="Laboratory Open Procotol Language",
    version="1.0a2",
    python_requires=">=3.8",
    install_requires=[
        "sbol3",
        "sparqlwrapper",
        "python-dateutil",
        "sbol-factory",
        "requests",
        "graphviz",
        "tyto>=1.3",
        "numpy",
        "openpyxl",
        "pint>=0.18",
        "requests_html",
        "container-ontology @ https://github.com/rpgoldman/container-ontology/tarball/main",
        "xarray>=0.20.2",
    ],
    tests_require=test_deps,
    extras_require=extras,
    packages=[
        "labop",
        "labop_convert",
        "labop_convert.autoprotocol",
        "labop_convert.markdown",
        "labop_convert.opentrons",
        "labop_convert.emeraldcloud",
        "labop.lib",
        "labop.inner",
        "labop.utils",
        "labop_time",
        "uml",
        "uml.inner",
        "examples",
        "owl_rdf_utils",
    ],
    package_data={
        "labop": ["inner/labop.ttl", "lib/*.ttl", "container-ontology.ttl"],
        "labop_convert": ["markdown/template.xlsx"],
        "uml": ["inner/uml.ttl"],
        "labop_time": ["labop_time.ttl"],
    },
    include_package_data=True,
)
