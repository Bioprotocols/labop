"""
Functions related to data i/o in connection with a protocol execution trace.

This file monkey-patches the imported labop classes with data handling functions.
"""

import json
import logging
from typing import Dict
from urllib.parse import quote, unquote

import sbol3
import xarray as xr

from labop.strings import Strings

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


def serialize_sample_format(data):
    if isinstance(data, xr.DataArray) or isinstance(data, xr.Dataset):
        data_dict = data.to_dict()
    elif isinstance(data, Dict):
        data_dict = data
    else:
        raise Exception(f"Cannot serialize sample_format of type: {type(data)}")
    return quote(json.dumps(data_dict))


def deserialize_sample_format(
    data: str, parent: sbol3.Identified = None, order=Strings.ROW_DIRECTION
):
    try:
        json_data = json.loads(unquote(data))
        try:
            xarray_data = xr.DataArray.from_dict(json_data)
            if parent:
                xarray_data.name = parent.identity
            return sort_samples(xarray_data, sample_format=Strings.XARRAY, order=order)
        except:
            try:
                xarray_data = xr.Dataset.from_dict(json_data)
                if Strings.SOURCE in xarray_data.coords:
                    xarray_data.coords[Strings.SOURCE] = [parent.identity]
                return sort_samples(
                    xarray_data, sample_format=Strings.XARRAY, order=order
                )
            except:
                return sort_samples(json_data, sample_format=Strings.JSON, order=order)
    except Exception as e:
        raise Exception(f"Could not determine format of data: {e}")


def sort_samples(data, sample_format=Strings.XARRAY, order=Strings.ROW_DIRECTION):
    if sample_format == Strings.XARRAY:
        if Strings.LOCATION in data.coords:
            data["row"] = data.coords["location"].str.slice(0, 1)
            data["col"] = data.coords["location"].str.slice(1).str.pad(2, fillchar="0")
            if order == Strings.ROW_DIRECTION:
                # for each row, for each col
                # A1->A12, B1->B12, ...
                data = data.sortby(["row", "col"])
            elif order == Strings.REVERSE_ROW_DIRECTION:
                # for each reverse(row) for each col
                # A12->A1, B12->B1, ...
                data = data.sortby("col", ascending=False).sortby("row")

            elif order == Strings.COLUMN_DIRECTION:
                # for each col for each row
                # A1->H1, A2->H2, ...
                data = data.sortby("row").sortby("col")
            elif order == Strings.REVERSE_COLUMN_DIRECTION:
                # for each reverse(col) for each row
                # H1->A1, H2->A2, ...
                data = data.sortby("row", ascending=False).sortby("col")
            data = data.drop_vars(["row", "col"])

    return data
