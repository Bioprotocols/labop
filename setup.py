from setuptools import setup

test_deps = ["nbmake", "pytest-xdist", "pre-commit", "nbstripout"]
notebook_deps = ["ipython", "ipywidgets"]
extras = {"test": test_deps, "notebook": notebook_deps}

setup(
    name="labop",
    description="Laboratory Open Procotol Language",
    version="1.0a2",
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
        "autoprotocol",
        "transcriptic",
        "pint>=0.18",
        "requests_html",
        "container-ontology @ https://github.com/rpgoldman/container-ontology/tarball/main",
        "xarray",
    ],
    python_requires=">=3.8",
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
        "labop.utils",
        "labop_time",
        "uml",
        "examples",
        "owl_rdf_utils",
    ],
    package_data={
        "labop": ["labop.ttl", "lib/*.ttl", "container-ontology.ttl"],
        "labop_convert": ["markdown/template.xlsx"],
        "uml": ["uml.ttl"],
        "labop_time": ["labop_time.ttl"],
    },
    include_package_data=True,
)
