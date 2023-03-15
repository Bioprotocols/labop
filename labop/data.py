"""
Functions related to data i/o in connection with a protocol execution trace.

This file monkey-patches the imported labop classes with data handling functions.
"""

import json
import logging
from cmath import nan
from itertools import islice
from typing import Dict
from urllib.parse import quote, unquote

import pandas as pd
import sbol3
import xarray as xr
from openpyxl import load_workbook

from labop.strings import Strings

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


def serialize_sample_format(data):
    data_str = None
    if isinstance(data, xr.DataArray) or isinstance(data, xr.Dataset):
        data_dict = data.to_dict()
    elif isinstance(data, Dict):
        data_dict = data
    else:
        raise Exception(f"Cannot serialize sample_format of type: {type(data)}")

    return quote(json.dumps(data_dict))


def deserialize_sample_format(data: str, parent: sbol3.Identified = None):
    try:
        json_data = json.loads(unquote(data))
        try:
            xarray_data = xr.DataArray.from_dict(json_data)
            if parent:
                xarray_data.name = parent.identity
            return sort_samples(xarray_data, sample_format=Strings.XARRAY)
        except:
            try:
                xarray_data = xr.Dataset.from_dict(json_data)
                if Strings.SOURCE in xarray_data.coords:
                    xarray_data.coords[Strings.SOURCE] = [parent.identity]
                return sort_samples(xarray_data, sample_format=Strings.XARRAY)
            except:
                return sort_samples(json_data, sample_format=Strings.JSON)
    except Exception as e:
        raise Exception(f"Could not determine format of data: {e}")


def sort_samples(data, sample_format=Strings.XARRAY):
    if sample_format == Strings.XARRAY:
        if Strings.SAMPLE in data.coords:
            data = (
                data.assign_coords(
                    samplez=(
                        "sample",
                        [
                            (f"{s[:1]}0{s[1:]}" if len(s) == 2 else s)
                            for s in data.coords["sample"].data
                        ],
                    )
                )
                .sortby("samplez")
                .reset_coords("samplez", drop=True)
            )
    return data
