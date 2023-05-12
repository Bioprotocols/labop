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
    "RELATIONS",
    "IGNORE_PROPERTIES",
]

import argparse
import logging
import os
import sys
from typing import Any, List, Optional, Set, Tuple

import rdflib as rdf
from rdflib import OWL, RDF, RDFS, Graph
from rdflib.term import Node

Triple = Tuple[Any, Any, Any]

# Properties of a restriction that indicate the actual constraint
RELATIONS = [
    OWL.allValuesFrom,
    OWL.someValuesFrom,
    OWL.minCardinality,
    OWL.maxCardinality,
    OWL.cardinality,
    OWL.hasValue,
    OWL.qualifiedCardinality,
]
# Properties of a restriction that we ignore when rewriting (because they are
# constraints ON the restrictions rather than constraints on the restrictED)
IGNORE_PROPERTIES = [OWL.onProperty, RDFS.comment, RDF.type]

CARDINALITY_RELS = [
    OWL.minCardinality,
    OWL.maxCardinality,
    OWL.cardinality,
    OWL.qualifiedCardinality,
]

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


PRINT_RELATIONS = [
    x.replace("http://www.w3.org/2002/07/owl#", "owl:") for x in RELATIONS
]
rc_explanation: str = (
    f": All restrictions must have one property from: {', '.join(PRINT_RELATIONS)}"
)


def is_bad_restr(restr: Node, graph: Graph) -> bool:
    """
    Is this an ill-formed restriction?
    """
    rrs: Set[Node] = set()
    rel: Node
    has_restricted: bool = False
    has_onClass: bool = False
    is_cardinality_rel: bool = False
    global rc_explanation  # pylint: disable=global-statement
    for _r, rel, _x in graph.triples((restr, None, None)):
        if rel == OWL.onProperty:
            has_restricted = True
        if rel in CARDINALITY_RELS:
            is_cardinality_rel = True
        if rel in RELATIONS:
            rrs.add(rel)
        if rel == OWL.onClass:
            has_onClass = True
    if not has_restricted:
        print(f"Need owl:onProperty in {restr}")
        return True
    if len(rrs) == 0:
        print(f"No components to restriction {restr}{rc_explanation}")
        rc_explanation = ""
        return True
    if len(rrs) > 1:
        restrs: str = ", ".join(
            [x.replace("http://www.w3.org/2002/07/owl#", "owl:") for x in rrs]
        )
        print(f"Multiple components to restriction {restr}: {restrs}")
        return True
    if has_onClass and not is_cardinality_rel:
        print("owl:onClass is only permissible in cardinality restrictions.")
    return False


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
    to_delete: List[Triple] = list(g.triples((b, None, None)))
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


def repair_all_bad_restrictions(
    g: rdf.Graph, bad: Optional[List[rdf.BNode]] = None
) -> Graph:
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


def repair_graph(
    bad: List[Node], graph: Graph, dry_run: bool, file=sys.stdout, format_name="turtle"
) -> None:
    if dry_run:
        if file != sys.stdout:
            LOGGER.addHandler(logging.StreamHandler(file))
        for x in bad:
            translate_bad_restr(x, graph)
    else:
        new_graph = repair_all_bad_restrictions(graph, bad)
        print(new_graph.serialize(format=format_name).decode(), file=file)


def main(
    *,
    infile: str,
    action: str,
    verbose: int = 0,
    quiet: bool = False,
    dry_run: bool = False,
    outfile: Optional[str] = None,
):
    if verbose == 1:
        LOGGER.setLevel(logging.INFO)
    elif verbose >= 2:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.WARNING)
    # log to standard error
    logging.basicConfig()

    assert os.path.exists(infile), f"No such file: {infile}"

    format_name = (
        rdf.util.guess_format(outfile) if outfile else rdf.util.guess_format(infile)
    )
    LOGGER.debug("Guessed format is %s", format_name)

    graph = rdf.Graph()
    graph.parse(infile, format=format_name)

    bad = all_bad_restrictions(graph)

    if action == "check":
        if bad:
            print("Found bad restrictions in graph")
            if not quiet:
                to_file: bool = False
                if outfile:
                    sys.stdout = open(outfile, "w")
                    to_file = True
                for b in bad:
                    describe_bad_restr(b, graph)
                if to_file:
                    sys.stdout.close()
            sys.exit(1)
        sys.exit(0)
    elif action == "repair":
        if not bad:
            print("No repairs needed", file=sys.stderr)
            sys.exit(1)
        if outfile:
            with open(outfile, "w") as file:
                repair_graph(bad, graph, dry_run, file)
        else:
            repair_graph(bad, graph, dry_run)


def process_args():
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
        action="store_true",
    )
    ap.add_argument(
        "--quiet",
        help="Don't print descriptions of bad restrictions: just set exit flag.",
        action="store_true",
    )

    values = ap.parse_args()
    verbose: int = getattr(values, "verbose", 0) or 0
    outfile = getattr(values, "output", None)
    main(
        action=values.action,
        infile=values.input,
        outfile=outfile,
        verbose=verbose,
        quiet=values.quiet,
        dry_run=values.dry_run,
    )


if __name__ == "__main__":
    process_args()
