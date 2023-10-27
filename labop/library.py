import os
import posixpath

import sbol3

from uml.utils import convert_to_outer_class

loaded_libraries = {}


def import_library(library: str, extension: str = "ttl", nickname: str = None):
    """Import a library of primitives and make it available for use in defining a protocol.

    Note that the actual contents of a library are added into a protocol document lazily, only as they're actually used
    TODO: this needs to be generalized to a notion of load paths, to allow other than built-in libraries

    :param library: name of library file to load
    :param extension: Format of library; defaults to ttl
    :param nickname: Name to load the library under; defaults to library name
    :return: Nothing
    """
    if not nickname:
        nickname = library
    if not os.path.isfile(library):
        library = posixpath.join(
            os.path.dirname(os.path.realpath(__file__)),
            f"lib/{library}.{extension}",
        )
    # read in the library and put the document in the library collection
    lib = sbol3.Document()
    lib.read(library, extension)
    # Convert each Primitive to an outer class

    # for o in lib.objects:
    #     o = convert_to_outer_class(
    #         o, package="labop"
    #     )  # Assume that lib only contains labop objects, such as Primitive

    loaded_libraries[nickname] = lib


def show_library(library_name: str):
    dashes = "-" * 80
    print(dashes)
    print(f"library: {library_name}")
    doc = loaded_libraries[library_name]
    for primitive in doc.objects:
        print(primitive)
    print(dashes)


def show_libraries():
    primitives = {}
    for lib in loaded_libraries.keys():
        show_library(lib)
