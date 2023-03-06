"""
Functions related to data i/o in connection with a protocol execution trace.

This file monkey-patches the imported labop classes with data handling functions.
"""

from cmath import nan
import xarray as xr
import json
from urllib.parse import quote, unquote

import labop
from labop_convert.plate_coordinates import coordinate_rect_to_row_col_pairs, coordinate_to_row_col
from labop import SampleMask, SampleData, SampleArray, SampleCollection
import uml
from typing import List, Dict


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
labop.ProtocolExecution.set_data = protocol_execution_set_data

def protocol_execution_get_data(self):
    """
    Gather labop.SampleData outputs from all CallBehaviorExecutions into a dataset
    """
    calls = [e for e in self.executions if isinstance(e, labop.CallBehaviorExecution)]
    datasets = { o.value.get_value().identity:
                    o.value.get_value().to_dataset()
                        for e in calls
                        for o in e.get_outputs()
                        if isinstance(o.value.get_value(), labop.SampleData)
    }

    return datasets
labop.ProtocolExecution.get_data = protocol_execution_get_data


def sample_array_to_data_array(self):
    return xr.DataArray.from_dict(json.loads(self.initial_contents))
SampleArray.to_data_array = sample_array_to_data_array


def sample_array_mask(self, mask):
    """
    Create a mask array out of SampleArray and mask.
    """
    def is_in_mask(entry, row_col_pairs):
        return entry in row_col_pairs

    if self.format == 'json':
        return mask
    elif self.format != 'xarray':
        raise Exception(f'Sample format {self.format} is not currently supported by the mask method')
    initial_contents_array = xr.DataArray.from_dict(json.loads(self.initial_contents))
    row_col_pairs = coordinate_rect_to_row_col_pairs(mask)
    mask_array = xr.DataArray(
                        [
                            is_in_mask(coordinate_to_row_col(x), row_col_pairs)
                            for x in initial_contents_array.data
                        ],
                        coords={Strings.ALIQUOT: initial_contents_array}
                    )
    return json.dumps(mask_array.to_dict())
SampleArray.mask = sample_array_mask


def sample_array_from_dict(self, initial_contents: dict):
    if self.format != 'json':
        raise Exception('Failed to write initial contents. The SampleArray initial contents are not configured for json format')
    self.initial_contents = quote(json.dumps(initial_contents))
    return self.initial_contents
SampleArray.from_dict = sample_array_from_dict


def sample_array_to_dict(self) -> dict:
    if self.format != 'json':
        raise Exception('Failed to dump initial contents to dict. The SampleArray initial contents do not appear to be json format')
    if not self.initial_contents:
        return {}
    if self.initial_contents == 'https://github.com/synbiodex/pysbol3#missing':
        return {}
    # De-serialize the initial_contents field of a SampleArray
    return json.loads(unquote(self.initial_contents))
SampleArray.to_dict = sample_array_to_dict


def sample_mask_to_data_array(self):
    return xr.DataArray.from_dict(json.loads(self.mask))
SampleMask.to_data_array = sample_mask_to_data_array


def sample_mask_get_coordinates(self):
    mask = self.to_data_array()
    return [c for c in mask.aliquot.data if mask.loc[c]]
SampleMask.get_coordinates = sample_mask_get_coordinates


def sample_array_get_coordinates(self):
    if self.format == 'json':
        return self.to_dict().values()
    elif self.format == 'xarray':
        initial_contents = self.to_data_array()
        return [c for c in initial_contents.aliquot.data]
    raise ValueError(f'Unsupported sample format: {self.format}')
SampleArray.get_coordinates = sample_mask_get_coordinates


def sample_collection_initialize_dataset(self, name: str):
    sample_array = self.to_data_array()

    sample_data = xr.Dataset({
                                name : xr.DataArray(
                                                [None]*len(sample_array[Strings.ALIQUOT]),
                                                [ (Strings.ALIQUOT, sample_array.coords[Strings.ALIQUOT].data) ]
                                            )})
    return sample_data
SampleCollection.initialize_dataset = sample_collection_initialize_dataset

def sample_mask_initialize_dataset(self, name: str):
    sample_array = self.to_data_array()
    sample_array = sample_array.where(sample_array, drop=True) # Apply mask

    sample_data = xr.Dataset({
                                name : xr.DataArray(
                                                [None]*len(sample_array[Strings.ALIQUOT]),
                                                [ (Strings.ALIQUOT, sample_array.coords[Strings.ALIQUOT].data) ]
                                            )})
    return sample_data
SampleMask.initialize_dataset = sample_mask_initialize_dataset


def sample_data_to_dataset(self):
    if hasattr(self, 'format') and self.format == 'json':
        raise NotImplementedError()
    if not hasattr(self, "values") or \
       not self.values:
        sample_data = self.from_samples.initialize_dataset(self.identity)
    else:
        sample_data = xr.Dataset.from_dict(json.loads(self.values))

    return sample_data
SampleData.to_dataset = sample_data_to_dataset

def sample_data_from_table(self, table: List[List[Dict[str, str]]]):
    """Convert from LabOPED table to SampleData

    Args:
        table (List[List[Dict]]): List of Rows.  Row is a List of attribute-value Dicts

    Returns:
        SampleData: labop.SampleData object encoded by table.
    """
    assert(len(table) > 1, "Cannot instantiate SampleData from table with fewer than 2 rows (need header and data).")


    # First row has the column headers
    col_headers = [x['value'] for x in table[0]]
    assert(len(col_headers) > 0, "Cannot instantiate SampleData from table with fewer than 1 column (need some data).")
    coord_cols = [i for i, x, in enumerate(col_headers) if x in ["Source", "Destination"]]

    coords = { col_headers[i] : [] for i in coord_cols }
    data = []
    for row in table[1:]:
        data.append([x['value'] for i, x in enumerate(row) if i not in coord_cols])
        for i, x in enumerate(row):
            if i in coord_cols:
                coords[col_headers[i]].append(x['value'])
        sample_data = xr.Dataset({
            self.identity : xr.DataArray(data, coords)
                            # [nan]*len(masked_array[Strings.ALIQUOT]),
                            # [ (Strings.ALIQUOT, masked_array.coords[Strings.ALIQUOT].data) ]
        })
        return sample_data
SampleData.from_table = sample_data_from_table

def activity_node_execution_get_outputs(self):
    return []
labop.ActivityNodeExecution.get_outputs = activity_node_execution_get_outputs

def call_behavior_execution_get_outputs(self):
    return [x for x in self.call.lookup().parameter_values
              if x.parameter.lookup().property_value.direction == uml.PARAMETER_OUT]
labop.CallBehaviorExecution.get_outputs = call_behavior_execution_get_outputs

def sample_array_plot(self, out_dir="out"):
    try:
        import matplotlib.pyplot as plt
        sa = self.to_data_array()
        # p = sa.plot.scatter(col="aliquot", x="contents")
        p = sa.plot()
        plt.savefig(f"{os.path.join(out_dir, self.name)}.pdf")
        return p
    except Exception as e:
        l.warning("Could not import matplotlib.  Install matplotlib to plot SampleArray objects.")
        return None
labop.SampleArray.plot = sample_array_plot

def sample_array_to_dot(self, dot, out_dir="out"):
    if self.plot(out_dir=out_dir):
        dot.node(self.name,
             _attributes={
                   "label" : f"<<table><tr><td><img src=\"{self.name}.pdf\"></img></td></tr></table>>"
                })
        return self.name
    else:
        dot.node(self.name)
        return self.name

labop.SampleArray.to_dot = sample_array_to_dot
def sample_metadata_to_dataarray(self: labop.SampleMetadata):
    return xr.DataArray.from_dict(json.loads(self.descriptions))
labop.SampleMetadata.to_dataarray = sample_metadata_to_dataarray

def dataset_to_dataset(self: labop.Dataset):
    """
    Join the self.data and self.metadata into a single xarray dataset.

    Parameters
    ----------
    self : labop.Dataset
        Dataset comprising data and metadata.
    """
    data = self.data.to_dataset()
    metadata = self.metadata.to_dataarray()
labop.Dataset.to_dataset = dataset_to_dataset
