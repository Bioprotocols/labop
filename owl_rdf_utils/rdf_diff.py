import argparse

from rdflib import Graph
from rdflib.util import guess_format
from rdflib.compare import IsomorphicGraph, to_isomorphic, graph_diff

ap = argparse.ArgumentParser()

ap.add_argument(
    "file1",
    help="file1 to compare.",
)

ap.add_argument(
    "file2",
    help="file2 to compare.",
)


def dump_nt_sorted(g: Graph):
    for l in sorted(g.serialize(format="nt").splitlines()):
        if l:
            print(l.decode("ascii"))


def main():
    values = ap.parse_args()
    format1 = guess_format(values.file1)
    format2 = guess_format(values.file2)
    g1: Graph = Graph().parse(values.file1, format=format1)
    g2: Graph = Graph().parse(values.file2, format=format2)
    iso1: IsomorphicGraph = to_isomorphic(g1)
    iso2: IsomorphicGraph = to_isomorphic(g2)
    _in_both, in_first, in_second = graph_diff(iso1, iso2)
    print(f"Only in {values.file1}")
    dump_nt_sorted(in_first)

    print(f"Only in {values.file2}")
    dump_nt_sorted(in_second)


if __name__ == "__main__":
    main()
