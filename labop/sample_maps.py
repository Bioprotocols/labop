"""
Functions related to sample map get and set.

This file monkey-patches the imported labop classes with data handling functions.
"""

import logging
from cmath import nan

import xarray as xr

import labop
import uml
from labop import SampleArray, SampleData, SampleMask
from labop.data import deserialize_sample_format, serialize_sample_format
from labop.utils.plate_coordinates import (
    coordinate_rect_to_row_col_pairs,
    coordinate_to_row_col,
    get_sample_list,
)

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


def sample_map_get_map(self):
    """
    Get the XArray DataArray from the values field.
    """
    if not hasattr(self, "values") or not self.values:
        raise Exception(
            "Don't know how to initialize a generic SampleMap.  Try a subclass."
        )
    else:
        sample_map = deserialize_sample_format(self.values, parent=self)
    return sample_map


labop.SampleMap.get_map = sample_map_get_map


def many_to_one_sample_map_get_map(self):
    """
    Get the XArray Dataset from the values field.
    """
    if not hasattr(self, "values") or not self.values:
        sources = [source.lookup() for source in self.sources]
        target = self.targets.lookup()

        aliquots = get_sample_list(
            geometry="A1:H12"
        )  # FIXME need to use the spec for each source and target
        source_to_target_arrays = {
            source.identity: xr.DataArray(
                [""] * len(aliquots),
                dims=(target.identity),
                coords={target.identity: aliquots},
            )
            for source in sources
        }

        sample_map = xr.Dataset(source_to_target_arrays)
    else:
        sample_map = labop.SampleMap.get_map()
    return sample_map


labop.ManyToOneSampleMap.get_map = many_to_one_sample_map_get_map


def one_to_many_sample_map_get_map(self):
    """
    Get the XArray Dataset from the values field.
    """
    if not hasattr(self, "values") or not self.values:
        source = self.sources
        targets = self.targets

        aliquots = get_sample_list(
            geometry="A1:H12"
        )  # FIXME need to use the spec for each source and target
        source_to_target_arrays = {
            target.identity: xr.DataArray(
                [""] * len(aliquots),
                dims=(source.identity),
                coords={source.identity: aliquots},
            )
            for target in targets
        }

        sample_map = xr.Dataset(source_to_target_arrays)
    else:
        sample_map = labop.SampleMap.get_map()
    return sample_map


labop.OneToManySampleMap.get_map = one_to_many_sample_map_get_map


def sample_map_set_map(self, sample_map):
    """
    Set the XArray Dataset to the values field.
    """
    self.values = serialize_sample_format(sample_map)


labop.SampleMap.set_map = sample_map_set_map
