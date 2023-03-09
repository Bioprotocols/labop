"""
Functions related to data i/o in connection with a protocol execution trace.

This file monkey-patches the imported labop classes with data handling functions.
"""

from cmath import nan
import xarray as xr
import pandas as pd
import json
from urllib.parse import quote, unquote
import os

import sbol3
import labop
from labop.strings import Strings
from labop_convert.plate_coordinates import get_sample_list

import uml
from typing import List, Dict, Union


import logging
l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


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

def sample_array_empty(self, geometry=None, sample_format=Strings.XARRAY):
    samples = get_sample_list(geometry) if geometry else []

    if sample_format == Strings.XARRAY:
        sample_array = xr.DataArray(
            samples,
            name=self.identity,
            dims=(Strings.SAMPLE),
            coords={Strings.SAMPLE: samples}
            )
    elif sample_format == Strings.JSON:
        sample_array = {s: None for s in samples}
    else:
        raise Exception(f"Cannot initialize contents of sample_format: {sample_format}")
    self.initial_contents = serialize_sample_format(sample_array)
    return sample_array
labop.SampleArray.empty = sample_array_empty


def sample_array_to_data_array(self, sample_format=Strings.XARRAY):
    if not hasattr(self, "initial_contents") or self.initial_contents is None:
        sample_array = self.empty(sample_format=sample_format)
    else:
        sample_array = deserialize_sample_format(self.initial_contents, parent=self)
    return sample_array
labop.SampleArray.to_data_array = sample_array_to_data_array


def sample_array_mask(self, mask, sample_format=Strings.XARRAY):
    """
    Create a mask array out of SampleArray and mask.
    """
    if sample_format == Strings.JSON:
        return mask
    elif sample_format == Strings.XARRAY:
        initial_contents_array = self.to_data_array(sample_format=sample_format)
        if isinstance(mask, labop.SampleMask):
            mask_array = mask.to_data_array(sample_format=sample_format)
        else:
            mask_coordinates = get_sample_list(mask)
            mask_array = xr.DataArray([m in mask_coordinates
                                       for m in initial_contents_array[Strings.SAMPLE].data],
                            name="mask",
                            dims=("sample"),
                            coords={"sample": initial_contents_array[Strings.SAMPLE].data})
        masked_array = initial_contents_array.where(mask_array, drop=True)
        return masked_array
    else:
        raise Exception(f'Sample format {self.sample_format} is not currently supported by the mask method')
labop.SampleArray.mask = sample_array_mask


def sample_array_from_dict(self, initial_contents: dict):
    if self.sample_format == 'json':
        self.initial_contents = serialize_sample_format(initial_contents)
    else:
        raise Exception('Failed to write initial contents. The SampleArray initial contents are not configured for json format')
    return self.initial_contents
labop.SampleArray.from_dict = sample_array_from_dict


def sample_array_to_dict(self, sample_format=Strings.XARRAY) -> dict:
    if sample_format == Strings.JSON:
        if not self.initial_contents:
            return {}
        if self.initial_contents == 'https://github.com/synbiodex/pysbol3#missing':
            return {}
        # De-serialize the initial_contents field of a SampleArray
        return json.loads(unquote(self.initial_contents))
    else:
        raise Exception('Failed to dump initial contents to dict. The SampleArray initial contents do not appear to be json format')
labop.SampleArray.to_dict = sample_array_to_dict


def sample_mask_empty(self, sample_format=Strings.XARRAY):
    if sample_format == "xarray":
        source_samples = self.source.lookup()
        sample_array = source_samples.to_data_array(sample_format=sample_format)
        mask_array = xr.DataArray(
            [True]*len(sample_array[Strings.SAMPLE]),
            name=self.identity,
            dims=(Strings.SAMPLE),
            coords={Strings.SAMPLE: sample_array.coords[Strings.SAMPLE].data}
            )
        self.mask = serialize_sample_format(mask_array)
    else:
        raise NotImplementedError()
    return mask_array
labop.SampleMask.empty = sample_mask_empty

def sample_mask_to_data_array(self, sample_format=Strings.XARRAY):
    if not hasattr(self, "mask") or self.mask is None:
        sample_mask = self.empty(sample_format=sample_format)
    else:
        sample_mask = deserialize_sample_format(self.mask, parent=self)
    return sample_mask
labop.SampleMask.to_data_array = sample_mask_to_data_array

def sample_mask_to_masked_data_array(self, sample_format=Strings.XARRAY):
    source = self.source.lookup()
    masked_array = source.mask(self)
    return masked_array
labop.SampleMask.to_masked_data_array = sample_mask_to_masked_data_array

def sample_mask_from_coordinates(source: labop.SampleCollection, coordinates: str, sample_format=Strings.XARRAY):
    mask = labop.SampleMask(source=source)
    mask_array = source.mask(coordinates, sample_format=sample_format)
    mask_array.name = mask.identity
    mask.mask = serialize_sample_format(mask_array)
    return mask
labop.SampleMask.from_coordinates = sample_mask_from_coordinates

def sample_mask_get_coordinates(self, sample_format=Strings.XARRAY):
    if sample_format == 'xarray':
        mask = self.to_data_array()
        return [c for c in mask[Strings.SAMPLE].data if mask.loc[c]]
    elif sample_format == 'json':
        return json.loads(deserialize_sample_format(self.mask)).keys()
labop.SampleMask.get_coordinates = sample_mask_get_coordinates


def sample_array_get_coordinates(self, sample_format=Strings.XARRAY):
    if sample_format == Strings.JSON:
        return self.to_dict(Strings.JSON).values()
    elif sample_format == Strings.XARRAY:
        initial_contents = self.to_data_array()
        return [c for c in initial_contents[Strings.SAMPLE].data]
    else:
        raise ValueError(f'Unsupported sample format: {self.sample_format}')
labop.SampleArray.get_coordinates = sample_array_get_coordinates

def sample_array_from_coordinates(source: labop.SampleCollection, coordinates: str, sample_type=Strings.XARRAY):
    mask = labop.SampleMask(source=source)
    mask_array = source.mask(coordinates)
    mask_array.name = mask.identity
    mask.mask = serialize_sample_format(mask_array)
    return mask
labop.SampleArray.from_coordinates = sample_array_from_coordinates

def sample_array_from_container_spec(container_type: labop.ContainerSpec, sample_format = Strings.XARRAY):
    sample_array = labop.SampleArray(container_type=container_type)

    if container_type.queryString == 'cont:Opentrons24TubeRackwithEppendorf1.5mLSafe-LockSnapcap':
        geometry = 'A1:C8'
    else:
        geometry = 'A1:H12'

    initial_contents = sample_array.empty(geometry=geometry, sample_format=sample_format)
    sample_array.initial_contents = serialize_sample_format(initial_contents)
    return sample_array
labop.SampleArray.from_container_spec = sample_array_from_container_spec

def sample_data_empty(self: labop.SampleData, sample_format=Strings.XARRAY):
    if sample_format == "xarray":
        from_samples = self.from_samples.lookup()
        sample_array = from_samples.to_data_array(sample_format=sample_format)
        sample_data = xr.DataArray(
            [nan]*len(sample_array[Strings.SAMPLE]),
            name=self.identity,
            dims=(Strings.SAMPLE),
            coords={Strings.SAMPLE: sample_array.coords[Strings.SAMPLE].data}
            )
        self.values = serialize_sample_format(sample_data)
    else:
        raise NotImplementedError()
    return sample_data
labop.SampleData.empty = sample_data_empty

def sample_data_to_data_array(self, sample_format=Strings.XARRAY):
    if not hasattr(self, "values") or self.values is None:
        sample_data = self.empty(sample_format=sample_format)
    else:
        sample_data = deserialize_sample_format(self.values, parent=self)
    return sample_data
labop.SampleData.to_data_array = sample_data_to_data_array

def sample_data_from_table(self, table: List[List[Dict[str, str]]]):
    """Convert from LabOPED table to SampleData

    Args:
        table (List[List[Dict]]): List of Rows.  Row is a List of attribute-value Dicts

    Returns:
        SampleData: labop.SampleData object encoded by table.
    """
    assert len(table) > 1, "Cannot instantiate SampleData from table with fewer than 2 rows (need header and data)."


    # First row has the column headers
    col_headers = [x['value'] for x in table[0]]
    assert len(col_headers) > 0, "Cannot instantiate SampleData from table with fewer than 1 column (need some data)."
    coord_cols = [i for i, x, in enumerate(col_headers) if x in ["Source", "Destination"]]

    coords = { col_headers[i] : [] for i in coord_cols }
    data = []
    for row in table[1:]:
        data.append([x['value'] for i, x in enumerate(row) if i not in coord_cols])
        for i, x in enumerate(row):
            if i in coord_cols:
                coords[col_headers[i]].append(x['value'])
        sample_data = xr.DataArray(data, coords)
                            # [nan]*len(masked_array[Strings.SAMPLE]),
                            # [ (Strings.SAMPLE, masked_array.coords[Strings.SAMPLE].data) ]

        return sample_data
labop.SampleData.from_table = sample_data_from_table

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
        name = self.name if (hasattr(self, "name") and self.name) else self.identity
        plt.savefig(f"{os.path.join(out_dir, name)}.pdf")
        return p
    except Exception as e:
        l.warning("Could not import matplotlib.  Install matplotlib to plot SampleArray objects.")
        return None
labop.SampleArray.plot = sample_array_plot

def sample_array_to_dot(self, dot, out_dir="out"):
    name = self.name if (hasattr(self, "name") and self.name) else self.identity
    if self.plot(out_dir=out_dir):
        dot.node(name,
             _attributes={
                   "label" : f"<<table><tr><td><img src=\"{name}.pdf\"></img></td></tr></table>>"
                })
        return name
    else:
        dot.node(name)
        return name

labop.SampleArray.to_dot = sample_array_to_dot
def sample_metadata_to_dataarray(self: labop.SampleMetadata):
    return xr.DataArray.from_dict(json.loads(self.descriptions))
labop.SampleMetadata.to_dataarray = sample_metadata_to_dataarray

def sample_metadata_empty(self, sample_format=Strings.XARRAY):
    if sample_format == Strings.XARRAY:
        sample_array = self.for_samples.lookup().to_data_array()
        # metadata_array = xr.DataArray(
        #     [nan]*len(sample_array[Strings.SAMPLE]),
        #     name=self.identity,
        #     dims=(Strings.SAMPLE),
        #     coords={Strings.SAMPLE: sample_array.coords[Strings.SAMPLE].data}
        #     )
        # self.descriptions = serialize_sample_format(metadata_array)
        # return metadata_array
        metadata_dataset = xr.Dataset(coords=sample_array.coords)
    else:
        raise NotImplementedError()
labop.SampleMetadata.empty = sample_metadata_empty

def sample_metadata_to_data_array(self: labop.SampleMetadata, sample_format=Strings.XARRAY):
    if not hasattr(self, "descriptions") or self.descriptions is None:
        metadata_array = self.empty(sample_format=sample_format)
    else:
        metadata_array = deserialize_sample_format(self.descriptions, parent=self)
    return metadata_array
labop.SampleMetadata.to_data_array = sample_metadata_to_data_array

def sample_metadata_from_excel(filename: Union[str, os.PathLike],
                               for_samples: labop.SampleCollection,
                               sample_format=Strings.XARRAY,
                               record_source=False):
    metadata = labop.SampleMetadata(for_samples=for_samples)
    metadata_df = pd.read_excel(filename)
    rename_map = {"Unnamed: 0": Strings.SAMPLE} if "Unnamed: 0" in metadata_df.columns else {}
    metadata_df = metadata_df.rename(rename_map, axis=1)
    # Assume that first column is the sample index
    metadata_df = metadata_df.set_index(metadata_df.columns[0])

    if sample_format == Strings.XARRAY:
        # Convert pd.DataFrame into xr.DataArray

        metadata_array = xr.Dataset.from_dataframe(metadata_df)
        if record_source:
            metadata_array = metadata_array.expand_dims({"source": [metadata.identity]}) # Will be replaced when deserilialized by parent.identity
        metadata.descriptions = serialize_sample_format(metadata_array)

        # The metadata_array is now a 2D xr.DataArray with dimensions (sample, metadata)
        # The sample coordinates are sample ids, and the metadata coordinates are metadata attributes
        # The name is the identity of the labop.SampleMetadata holding the metadata_array
    else:
        raise NotImplementedError(f"Cannot represent Excel SampleMetadata as sample_format: {sample_format}")

    return metadata
labop.SampleMetadata.from_excel = sample_metadata_from_excel

def sample_metadata_for_primitive(primitive: labop.Primitive,
                                  inputs: Dict[str, sbol3.Identified],
                                  for_samples: labop.SampleCollection,
                                  sample_format=Strings.XARRAY,
                                  record_source=False):


    metadata = labop.SampleMetadata(for_samples=for_samples)
    # metadata_array = metadata.empty(sample_format=sample_format)

    if sample_format == Strings.XARRAY:
        sample_array = for_samples.to_data_array()

        # Create new metadata for each input to primitive, aside from for_samples
        inputs_meta = {k: xr.DataArray(
                [v.identity]*len(sample_array.coords[Strings.SAMPLE]),
                dims=Strings.SAMPLE,
                coords=sample_array.coords
            )
            for k, v in inputs.items() if v != for_samples
        }

        metadata_dataset = xr.Dataset(inputs_meta, coords=sample_array.coords)
        if record_source:
            metadata_dataset = metadata_dataset.expand_dims({"source": [metadata.identity]})

    elif sample_format == Strings.JSON:
        metadata_dataset = {}
    else:
        raise NotImplementedError(f"Cannot represent {primitive} SampleMetadata as sample_format: {sample_format}")

    metadata.descriptions = serialize_sample_format(metadata_dataset)

    return metadata
labop.SampleMetadata.for_primitive = sample_metadata_for_primitive

def dataset_to_dataset(self: labop.Dataset, sample_format=Strings.XARRAY):
    """
    Join the self.data and self.metadata into a single xarray dataset.

    Parameters
    ----------
    self : labop.Dataset
        Dataset comprising data and metadata.
    """
    data = [self.data.to_data_array(sample_format=sample_format)] if self.data else []
    datasets = [d.lookup().to_dataset(sample_format=sample_format) for d in self.dataset] if self.dataset else []
    metadata = [m.to_data_array(sample_format=sample_format) for m in self.metadata] if self.metadata else []
    linked_metadata = [m.lookup().to_data_array(sample_format=sample_format) for m in self.linked_metadata] if self.linked_metadata else []
    to_merge = data + metadata + datasets + linked_metadata
    ds = xr.merge(to_merge)
    return ds
labop.Dataset.to_dataset = dataset_to_dataset

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
            return xarray_data
        except:
            try:
                xarray_data = xr.Dataset.from_dict(json_data)
                if Strings.SOURCE in xarray_data.coords:
                    xarray_data.coords[Strings.SOURCE] = [parent.identity]
                return xarray_data
            except:
                return json_data
    except Exception as e:
        raise Exception(f"Could not determine format of data: {e}")

def sort_samples(data):
    data = data.assign_coords(
        samplez=("sample",
                 [(f"{s[:1]}0{s[1:]}" if len(s) == 2 else s) for s in data.coords["sample"].data])
    ).sortby("samplez").reset_coords("samplez", drop=True)
    return data


def sample_data_update_data_sheet(self, data_file_path, sheet_name, sample_format=Strings.XARRAY):
    sample_array = labop.sort_samples(labop.deserialize_sample_format(self.values, parent=self))

    # Check whether data exists in the data template, and load it
    changed = False
    if os.path.exists(data_file_path):
        try:
            data_df = pd.read_excel(data_file_path, sheet_name=sheet_name)
            # Assume that first column is the sample index
            data_df = data_df.set_index(data_df.columns[0])
            if sample_format == Strings.XARRAY:
                # Convert pd.DataFrame into xr.DataArray
                sample_data_array = xr.Dataset.from_dataframe(data_df)[sample_array.name]

                changed =  not(
                    (sample_array.isnull().all() and sample_data_array.isnull().all()) or \
                            (sample_data_array == sample_array).all()
                )
                if changed:
                    sample_array = sample_data_array
                    self.values = labop.serialize_sample_format(sample_array)

            else:
                raise Exception(f"Cannot read sample_format {sample_format} from Excel")
        except Exception as e:
            # Sheet could not be loaded, so it did not change
            pass

    if not changed:
        mode = "a" if os.path.exists(data_file_path) else "w"
        kwargs = {"if_sheet_exists":"replace"} if mode == "a" else {}
        # kwargs['strings_to_formulas'] = False
        # kwargs['strings_to_urls'] = False
        with pd.ExcelWriter(
            data_file_path,
            mode=mode,
            engine="openpyxl",
            **kwargs
            ) as writer:
            sample_array.to_dataframe().to_excel(
                writer,
                sheet_name=sheet_name
                )
labop.SampleData.update_data_sheet = sample_data_update_data_sheet

def dataset_update_data_sheet(self, data_file_path, sheet_name, sample_format=Strings.XARRAY):
    dataset = sort_samples(self.to_dataset())

    # # Check whether data exists in the data template, and load it
    # changed = False
    # if os.path.exists(data_file_path):
    #     try:
    #         data_df = pd.read_excel(data_file_path, sheet_name=sheet_name)
    #         # Assume that first column is the sample index
    #         data_df = data_df.set_index(data_df.columns[0])
    #         if sample_format == Strings.XARRAY:
    #             # Convert pd.DataFrame into xr.DataArray
    #             stored_dataset = xr.Dataset.from_dataframe(data_df)

    #             changed =  not(
    #                 (dataset.isnull().all() and stored_dataset.isnull().all()) or \
    #                         (stored_dataset == dataset).all()
    #             )
    #             if changed:
    #                 dataset = stored_dataset
    #                 self.values = labop.serialize_sample_format(sample_array)

    #         else:
    #             raise Exception(f"Cannot read sample_format {sample_format} from Excel")
    #     except Exception as e:
    #         # Sheet could not be loaded, so it did not change
    #         pass

    # if not changed:
    mode = "a" if os.path.exists(data_file_path) else "w"
    kwargs = {"if_sheet_exists":"replace"} if mode == "a" else {}
    # kwargs['strings_to_formulas'] = False
    # kwargs['strings_to_urls'] = False
    with pd.ExcelWriter(
        data_file_path,
        mode=mode,
        engine="openpyxl",
        **kwargs
        ) as writer:
        dataset.to_dataframe().to_excel(
            writer,
            sheet_name=sheet_name
            )
labop.Dataset.update_data_sheet = dataset_update_data_sheet
