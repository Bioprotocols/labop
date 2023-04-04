import dataclasses
import datetime
import hashlib
import importlib
import json
from typing import Union

import sbol3

from .literal_boolean import LiteralBoolean
from .literal_identified import LiteralIdentified
from .literal_integer import LiteralInteger
from .literal_null import LiteralNull
from .literal_real import LiteralReal
from .literal_reference import LiteralReference
from .literal_specification import LiteralSpecification
from .literal_string import LiteralString


# Workaround for pySBOL3 issue #231: should be applied to every iteration on a collection of SBOL objects
# TODO: delete after resolution of pySBOL3 issue #231
def id_sort(i: iter):
    sortable = list(i)
    sortable.sort(key=lambda x: x.identity if isinstance(x, sbol3.Identified) else x)
    return sortable


###########################################
# Define extension methods for ValueSpecification


def literal(
    value: Union[
        str,
        LiteralReference,
        LiteralNull,
        None,
        bool,
        int,
        float,
        sbol3.TopLevel,
        sbol3.Identified,
    ],
    reference: bool = False,
) -> LiteralSpecification:
    """Construct a UML LiteralSpecification based on the value of the literal passed

    Parameters
    ----------
    value: the value to embed as a literal
    reference: if true, use a reference for a non-TopLevel SBOL rather than embedding as a child object

    Returns
    -------
    LiteralSpecification of the appropriate type for the value
    """
    if isinstance(value, LiteralReference):
        return literal(
            value.value.lookup(), reference
        )  # if it's a reference, make co-reference
    elif isinstance(value, LiteralNull):
        return LiteralNull()
    elif isinstance(value, LiteralSpecification):
        return literal(value.value, reference)  # if it's a literal, unwrap and rebuild
    elif value is None:
        return LiteralNull()
    elif isinstance(value, str):
        return LiteralString(value=value)
    elif isinstance(value, bool):
        return LiteralBoolean(value=value)
    elif isinstance(value, int):
        return LiteralInteger(value=value)
    elif isinstance(value, float):
        return LiteralReal(value=value)
    elif isinstance(value, sbol3.TopLevel) or (
        reference and isinstance(value, sbol3.Identified)
    ):
        return LiteralReference(value=value)
    elif isinstance(value, sbol3.Identified):
        return LiteralIdentified(value=value)
    else:
        raise ValueError(
            f'Don\'t know how to make literal from {type(value)} "{value}"'
        )


def labop_hash(obj):
    def json_default(thing):
        try:
            return dataclasses.asdict(thing)
        except TypeError:
            pass
        if isinstance(thing, datetime.datetime):
            return thing.isoformat(timespec="microseconds")
        raise TypeError(f"object of type {type(thing).__name__} not serializable")

    def json_dumps(thing):
        return json.dumps(
            thing,
            default=json_default,
            ensure_ascii=False,
            sort_keys=True,
            indent=None,
            separators=(",", ":"),
        )

    j = int(hashlib.md5(json_dumps(obj).encode("utf-8")).digest().hex(), 16)
    return j


def inner_to_outer(inner_class, package="uml"):
    # Convert the inner class into an outer class
    labop_module = importlib.import_module(package)
    labop_class = getattr(labop_module, type(inner_class).__name__)
    return labop_class


def convert_to_outer_class(inner_class, package="uml"):
    try:
        inner_class.__class__ = inner_to_outer(inner_class, package=package)
    except:
        pass
    return inner_class
