"""
Functions related to data i/o in connection with a protocol execution trace.

This file monkey-patches the imported paml classes with data handling functions.
"""

from cmath import nan
import xarray as xr
import json

import paml
from paml_convert.plate_coordinates import coordinate_rect_to_row_col_pairs, coordinate_to_row_col
from paml import SampleMask, SampleData, SampleArray
import uml

import logging
l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)

class Strings:
    ALIQUOT = "aliquot"

def protocol_execution_set_data(self, dataset):
    """
    Overwrite execution trace values based upon values provided in data
    """
    for k, v in dataset.items():
        sample_data = self.document.find(k)
        sample_data.values = json.dumps(v.to_dict())
paml.ProtocolExecution.set_data = protocol_execution_set_data

def protocol_execution_get_data(self):
    """
    Gather paml.SampleData outputs from all CallBehaviorExecutions into a dataset
    """
    def output_value(o):
        return o.value.value.lookup() if isinstance(o.value, uml.LiteralReference) else o.value.value

    calls = [e for e in self.executions if isinstance(e, paml.CallBehaviorExecution)]
    datasets = [
                    output_value(o).to_dataset()
                        for e in calls
                        for o in e.get_outputs()
                        if isinstance(output_value(o), paml.SampleData)
                ]
    data = xr.merge(datasets)

    return data
paml.ProtocolExecution.get_data = protocol_execution_get_data


def sample_array_to_data_array(self):
    return xr.DataArray.from_dict(json.loads(self.contents))
SampleArray.to_data_array = sample_array_to_data_array

def sample_array_mask(self, mask):
    """
    Create a mask array out of SampleArray and mask.
    """
    def is_in_mask(entry, row_col_pairs):
        return entry in row_col_pairs

    contents_array = xr.DataArray.from_dict(json.loads(self.contents))
    row_col_pairs = coordinate_rect_to_row_col_pairs(mask)
    mask_array = xr.DataArray(
                        [
                            is_in_mask(coordinate_to_row_col(x), row_col_pairs)
                            for x in contents_array.data
                        ],
                        coords=[(Strings.ALIQUOT, contents_array.data)]
                    )
    return json.dumps(mask_array.to_dict())
SampleArray.mask = sample_array_mask


def sample_mask_to_data_array(self):
    return xr.DataArray.from_dict(json.loads(self.mask))
SampleMask.to_data_array = sample_mask_to_data_array


def sample_mask_get_coordinates(self):
    mask = self.to_data_array()
    return [c for c in mask.aliquot.data if mask.loc[c]]
SampleMask.get_coordinates = sample_mask_get_coordinates


def sample_array_get_coordinates(self):
    contents = self.to_data_array()
    return [c for c in contents.aliquot.data]
SampleArray.get_coordinates = sample_mask_get_coordinates


def sample_data_to_dataset(self):
    if not hasattr(self, "values") or \
       not self.values:
        from_samples = self.from_samples.lookup()
        sample_array = from_samples.to_data_array()
        masked_array = sample_array.where(sample_array, drop=True) # Apply the mask

        # Each dataset maps uses self.identity to write back any
        # new values to self.
        sample_data = xr.Dataset({
                                    self.identity : xr.DataArray(
                                                    [nan]*len(masked_array[Strings.ALIQUOT]),
                                                    [ (Strings.ALIQUOT, masked_array.coords[Strings.ALIQUOT].data) ]
                                                )})
    else:
        sample_data = xr.Dataset.from_dict(json.loads(self.values))

    return sample_data
SampleData.to_dataset = sample_data_to_dataset

def activity_node_execution_get_outputs(self):
    return []
paml.ActivityNodeExecution.get_outputs = activity_node_execution_get_outputs

def call_behavior_execution_get_outputs(self):
    return [x for x in self.call.lookup().parameter_values
              if x.parameter.lookup().property_value.direction == uml.PARAMETER_OUT]
paml.CallBehaviorExecution.get_outputs = call_behavior_execution_get_outputs
