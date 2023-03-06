"""
Functions related to sample map get and set.

This file monkey-patches the imported labop classes with data handling functions.
"""

from cmath import nan
import xarray as xr
import json

import labop
from labop_convert.plate_coordinates import coordinate_rect_to_row_col_pairs, coordinate_to_row_col, get_aliquot_list
from labop import SampleMask, SampleData, SampleArray
import uml

import logging
l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


def sample_map_get_map(self):
    """
    Get the XArray DataArray from the values field.
    """
    if not hasattr(self, "values") or \
       not self.values:
        raise Exception("Don't know how to initialize a generic SampleMap.  Try a subclass.")
    else:
        sample_map = xr.DataArray.from_dict(json.loads(self.values))
    return sample_map
labop.SampleMap.get_map = sample_map_get_map

def sample_map_set_map(self, sample_map):
    """
    Set the XArray Dataset to the values field.
    """
    self.values = json.dumps(sample_map.to_dict())
labop.SampleMap.set_map = sample_map_set_map
