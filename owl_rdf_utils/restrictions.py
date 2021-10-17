#!/usr/bin/env python
# coding: utf-8

"""
Utilities for manipulating and correcting OWL files in RDF.
"""

__all__ = [
    "all_restrictions",
    "is_bad_restr",
    "describe_bad_restr",
    "translate_bad_restr",
    "all_bad_restrictions",
    "repair_graph",
    "repair_all_bad_restrictions",
]

import argparse
import logging
import os
import sys

from copy import deepcopy

import rdflib as rdf
from rdflib import OWL, RDF, RDFS, Graph
from rdflib.term import Node
from rdflib.namespace import NamespaceManager

from typing import List, Tuple, Optional, Any, Set

Triple = Tuple[Any, Any, Any]

# Properties of a restriction that indicate the actual constraint
RELATIONS = [
    OWL.allValuesFrom,
    OWL.someValuesFrom,
    OWL.minCardinality,
    OWL.maxCardinality,
    OWL.cardinality,
]
# Properties of a restriction that we ignore when rewriting (because they are constraints ON
# the restrictions rather than constraints on the restrictED
IGNORE_PROPERTIES = [OWL.onProperty, RDFS.comment, RDF.type]

RESTRICTIONS_QUERY = (
    """
    PREFIX owl: <%s>

    SELECT ?r
    {
        ?r a owl:Restriction .
    }
"""
    % rdf.OWL
)

LOGGER = logging.getLogger(__name__)


def all_restrictions(graph: Graph) -> List[Node]:
    """Return a list of the nodes naming owl:Restrictions."""
    return [r["r"] for r in graph.query(RESTRICTIONS_QUERY)]


def is_bad_restr(restr: Node, graph: Graph) -> bool:
    """
    Is this an ill-formed restriction?
    """
    rrs: Set[Node] = set()
    rel: Node
    for _r, rel, _x in graph.triples((restr, None, None)):
        if rel in RELATIONS:
            rrs.add(rel)
    assert len(rrs) > 0, f"No components to restriction {restr}"
    return len(rrs) > 1


def describe_bad_restr(b: Node, g: Graph) -> None:
    """Print description of a bad restriction to sys.stdout"""
    nsm = rdf.namespace.NamespaceManager(g)
    nsm.bind("owl", OWL)
    triples = g.triples((b, None, None))
    for x, _y, z in g.triples((b, RDF.type, None)):
        print("%s a %s" % (x, z))
    for _, y, z in triples:
        if y not in {RDFS.comment, RDF.type}:
            print("\t%s %s" % (nsm.normalizeUri(y), nsm.normalizeUri(z)))
    for x, _y, z in g.triples((b, RDFS.comment, None)):
        print("\t%s rdfs:comment %s" % (x, z))
    print()


def translate_bad_restr(b: Node, g: Graph) -> Tuple[List[Triple], List[Triple]]:
    """
    Return a list of RDF triples to be added and removed to repair a bad restriction.

    The triples to be removed are the triples describing the bad restriction, and triples
    indicating that some OWL class inherits from the bad restriction.

    The triples to be added are triples that create a set of well-formed restrictions,
    one per constraint, and triples that indicate subclasses of those restrictions.

    Parameters
    ----------
    b : rdflib.term.Node
       Node designating a restriction that is ill-formed and must be repaired.
    g : rdflib.Graph
       Graph containing the restriction to be repaired.

    Returns
    -------
    to_add, to_delete : Tuple whose first element is a list of triples to be added
      to `g`, and whose second is a list of triples to be removed.
    """
    comment: Optional[Any] = None
    new_bnodes: List[rdf.BNode] = []
    to_add: List[Triple] = []
    to_delete: List[Triple] = [tuple for tuple in g.triples((b, None, None))]
    nsm = rdf.namespace.NamespaceManager(g)
    nsm.bind("owl", OWL)

    def normalize(x):
        return nsm.normalizeUri(x)

    def find_children() -> List[Node]:
        child_triples = g.triples((None, RDFS.subClassOf, b))
        children = [x for x, _, _ in child_triples]
        assert len(children) >= 1
        return children

    triples: List[Triple] = g.triples((b, None, None))
    types: List[Node] = [z for _x, _y, z in g.triples((b, RDF.type, None))]
    props: List[Node] = [z for _x, _y, z in g.triples((b, OWL.onProperty, None))]
    comments: List[Node] = [z for _x, _y, z in g.triples((b, RDFS.comment, None))]
    assert len(props) == 1
    assert len(comments) <= 1
    assert len(types) == 1
    prop = props[0]
    if comments:
        comment = comments[0]

    for _, y, z in triples:
        if y not in set(IGNORE_PROPERTIES) | {RDF.type}:
            bnode: rdf.BNode = rdf.BNode()
            new_bnodes.append(bnode)
            LOGGER.info(f"{nsm.normalizeUri(bnode)} a {nsm.normalizeUri(types[0])} ;")
            to_add.append((bnode, RDF.type, types[0]))
            LOGGER.info(f"\towl:onProperty {nsm.normalizeUri(prop)} ;")
            to_add.append((bnode, OWL.onProperty, prop))
            msg = f"\t{nsm.normalizeUri(y)} {nsm.normalizeUri(z)}"
            to_add.append((bnode, y, z))
            if comment:
                msg += f"\n\trdfs:comment {comment} ."
                to_add.append((bnode, RDFS.comment, comment))
            else:
                msg += " ."
            LOGGER.info(msg)
    LOGGER.info("Children of this restriction are:")
    for x in find_children():
        LOGGER.info(f"\t{x}")
        LOGGER.info(f"\tRemove {normalize(x)} rdfs:subClassOf {normalize(b)}")
        to_delete.append((x, RDFS.subClassOf, b))
        for nb in new_bnodes:
            LOGGER.info(
                f"\t{x} {nsm.normalizeUri(RDFS.subClassOf)} {nsm.normalizeUri(nb)}"
            )
            to_add.append((x, RDFS.subClassOf, nb))

    return to_add, to_delete


def all_bad_restrictions(g: Graph) -> List[Node]:
    """List of all bad restrictions in graph."""
    restrs = all_restrictions(g)
    return [r for r in restrs if is_bad_restr(r, g)]


def repair_all_bad_restrictions(g: rdf.Graph, bad: Optional[List[rdf.BNode]] = None):
    if bad is None:
        bad = all_bad_restrictions(g)
    all_adds: List[Triple] = []
    all_deletes: List[Triple] = []
    for x in bad:
        to_add, to_delete = translate_bad_restr(x, g)
        all_adds += to_add
        all_deletes += to_delete
    for x in all_adds:
        g.add(x)
    for x in all_deletes:
        g.remove(x)
    return g


def repair_graph(bad: List[Node], graph: Graph, dry_run: bool, file=sys.stdout, format='turtle'):
    if dry_run:
        if file != sys.stdout:
            LOGGER.addHandler(logging.StreamHandler(file))
        for x in bad:
            translate_bad_restr(x, graph)
    else:
        new_graph = repair_all_bad_restrictions(graph, bad)
        print(new_graph.serialize(format=format).decode(), file=file)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "action",
        help="Action to perform.",
        choices=["check", "repair"],
        default="check",
    )
    ap.add_argument("input", help="File containing RDF graph to check")
    ap.add_argument(
        "--output", "-o", help="Write repaired RDF graph or check results here."
    )
    ap.add_argument("--verbose", "-v", dest="verbose", action="count")
    ap.add_argument(
        "--dry-run",
        help="If repairing, just print the set of changes to be made, don't write output.",
    )
    ap.add_argument(
        "--quiet",
        help="Don't print descriptions of bad restrictions: just set exit flag.",
        action="store_true",
    )

    values = ap.parse_args()
    verbose: Optional[int] = getattr(values, "verbose", 0) or 0
    if verbose == 1:
        LOGGER.setLevel(logging.INFO)
    elif verbose >= 2:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.WARNING)
    # log to standard error
    logging.basicConfig()

    infile = values.input
    outfile = getattr(values, "output", None)
    assert os.path.exists(infile), f"No such file: {infile}"

    format = rdf.util.guess_format(outfile) if outfile else rdf.util.guess_format(infile)
    LOGGER.debug("Guessed format is %s", format)

    graph = rdf.Graph()
    graph.parse(infile, format=format)

    bad = all_bad_restrictions(graph)

    if values.action == "check":
        if bad:
            print("Found bad restrictions in graph")
            if not values.quiet:
                to_file: bool = False
                if hasattr(values, "output") and values.output:
                    sys.stdout == open(values.output, "w")
                    to_file = True
                for b in bad:
                    describe_bad_restr(b, graph)
                if to_file:
                    sys.stdout.close()
            sys.exit(1)
        sys.exit(0)
    elif values.action == "repair":
        if not bad:
            print("No repairs needed", file=sys.stderr)
            sys.exit(1)
        if hasattr(values, "output") and values.output:
            with open(values.output, "w") as file:
                repair_graph(bad, graph, values.dry_run, file)
        else:
            repair_graph(bad, graph, values.dry_run)


if __name__ == "__main__":
    main()
