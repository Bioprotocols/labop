import argparse
import os
from typing import List, Optional, Union

from rdflib import Graph

NTRIPLES = "nt"

__all__ = ["to_ntriples"]


def to_ntriples(graph: Graph) -> str:
    """Return sorted n-triples representation of graph."""
    # have RDFlib give us the ntriples as a string
    nt_text: bytes = graph.serialize(format=NTRIPLES)
    nt_string = nt_text.decode()
    # split it into lines
    lines = nt_string.splitlines(keepends=True)
    # sort those lines
    lines.sort()
    # write out the lines
    # RDFlib gives us bytes, so open file in binary mode
    return join_lines(lines)


def join_lines(lines: List[Union[bytes, str]]) -> str:
    if isinstance(lines[0], bytes):
        return b"\n".join([line.strip() for line in lines])
    return "\n".join([line.strip() for line in lines])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="File containing RDF graph to translate")
    ap.add_argument("--output", "-o",
                    help="Write RDF graph as sorted n-triples here.")
    values = ap.parse_args()
    infile = values.input
    assert os.path.exists(infile), f"No such file: {infile}"

    graph = Graph()
    _, ext = os.path.splitext(infile)
    print(ext)
    format_name: Optional[str] = None
    if ext == ".ttl":
        format_name = "turtle"
    graph.parse(infile, format=format_name)
    new_graph: Union[bytes, str] = to_ntriples(graph)
    if isinstance(new_graph, bytes):
        new_graph = new_graph.decode()
    new_graph = new_graph.replace("\\n", "\n")
    if hasattr(values, "output") and values.output:
        with open(values.output, "w") as file:
            print(new_graph, file=file)
    else:
        print(new_graph)


if __name__ == "__main__":
    main()
