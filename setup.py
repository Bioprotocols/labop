from setuptools import find_packages, setup

test_deps = [
    "nbmake",
    "pytest-xdist",
    "pre-commit",
    "nbstripout",
    "parameterized",
]
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
    packages=find_packages("src", exclude=["*attic", "examples"]),
    package_data={
        "labop": ["inner/labop.ttl", "lib/*.ttl", "container-ontology.ttl"],
        "labop_convert": ["markdown/template.xlsx"],
        "uml": ["inner/uml.ttl"],
        "labop_time": ["labop_time.ttl"],
    },
    package_dir={"": "src"},
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "labop=labop_cli.commands:main",
        ],
    },
)
