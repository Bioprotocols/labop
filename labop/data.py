"""
Functions related to data i/o in connection with a protocol execution trace.

This file monkey-patches the imported labop classes with data handling functions.
"""

import json
import logging
import os
from cmath import nan
from itertools import islice
from typing import Dict, List, Union
from urllib.parse import quote, unquote

import numpy as np
import pandas as pd
import sbol3
import xarray as xr
from openpyxl import load_workbook

import labop
import uml
from labop.strings import Strings
from labop.utils.plate_coordinates import contiguous_coordinates, get_sample_list

l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)


def new_sample_id() -> int:
    return f"{Strings.SAMPLE}_{labop.new_uuid()}"


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
    datasets = {
        o.value.get_value().identity: o.value.get_value().to_dataset()
        for e in calls
        for o in e.get_outputs()
        if isinstance(o.value.get_value(), labop.SampleData)
    }

    return datasets


labop.ProtocolExecution.get_data = protocol_execution_get_data


def sample_array_empty(self, geometry=None, sample_format=Strings.XARRAY):
    locations = get_sample_list(geometry) if geometry else []
    samples = [new_sample_id() for l in locations]

    if sample_format == Strings.XARRAY:
        sample_array = xr.Dataset(
            {
                Strings.CONTENTS: xr.DataArray(
                    [[[]] * len(locations)],
                    dims=(
                        Strings.CONTAINER,
                        Strings.LOCATION,
                        Strings.REAGENT,
                    ),
                ),
                Strings.SAMPLE_LOCATION: xr.DataArray(
                    [samples],
                    dims=(Strings.CONTAINER, Strings.LOCATION),
                ),
            },
            coords={
                Strings.SAMPLE: samples,
                Strings.REAGENT: [],
                Strings.CONTAINER: [self.container_type],
                Strings.LOCATION: locations,
            },
        )
    elif sample_format == Strings.JSON:
        sample_array = {s: None for s in locations}
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
            masked_array = mask.to_data_array(sample_format=sample_format)
        else:
            mask_coordinates = get_sample_list(mask)
            # Mask the data variables
            mask_array = initial_contents_array.where(
                initial_contents_array.location.isin(mask_coordinates),
                drop=True,
            )
            # Remove unused coordinates
            masked_array = mask_array.assign_coords(
                {
                    Strings.SAMPLE: mask_array.sample.where(
                        mask_array.sample.isin(mask_array.sample_location),
                        drop=True,
                    )
                }
            )
        return masked_array
    else:
        raise Exception(
            f"Sample format {self.sample_format} is not currently supported by the mask method"
        )


labop.SampleArray.mask = sample_array_mask


def sample_array_from_dict(self, initial_contents: dict):
    if self.sample_format == "json":
        self.initial_contents = serialize_sample_format(initial_contents)
    else:
        raise Exception(
            "Failed to write initial contents. The SampleArray initial contents are not configured for json format"
        )
    return self.initial_contents


labop.SampleArray.from_dict = sample_array_from_dict


def sample_array_to_dict(self, sample_format=Strings.XARRAY) -> dict:
    if sample_format == Strings.JSON:
        if not self.initial_contents:
            return {}
        if self.initial_contents == "https://github.com/synbiodex/pysbol3#missing":
            return {}
        # De-serialize the initial_contents field of a SampleArray
        return json.loads(unquote(self.initial_contents))
    else:
        raise Exception(
            "Failed to dump initial contents to dict. The SampleArray initial contents do not appear to be json format"
        )


labop.SampleArray.to_dict = sample_array_to_dict


def sample_array_from_ordering(samples: labop.SampleCollection, order: str):
    return labop.SampleArray(
        container_type=samples.get_container_type(),
        initial_contents=serialize_sample_format(
            xr.merge(
                [
                    samples.to_data_array(),
                    deserialize_sample_format(order, parent=samples),
                ]
            )
        ),
    )


labop.SampleArray.from_ordering = sample_array_from_ordering


def sample_mask_empty(self, sample_format=Strings.XARRAY):
    if sample_format == "xarray":
        source_samples = self.source.lookup()
        sample_array = source_samples.to_data_array(sample_format=sample_format)
        mask_array = xr.DataArray(
            [True] * len(sample_array[Strings.SAMPLE]),
            name=self.identity,
            dims=(Strings.SAMPLE),
            coords={Strings.SAMPLE: sample_array.coords[Strings.SAMPLE].data},
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


def sample_mask_from_coordinates(
    source: labop.SampleCollection,
    coordinates: str,
    sample_format=Strings.XARRAY,
):
    mask = labop.SampleMask(source=source)
    mask_array = source.mask(coordinates, sample_format=sample_format)
    mask.mask = serialize_sample_format(mask_array)
    return mask


labop.SampleMask.from_coordinates = sample_mask_from_coordinates


def sample_mask_get_coordinates(self, sample_format=Strings.XARRAY):
    if sample_format == "xarray":
        mask = self.to_data_array()
        return mask.location.data.tolist()
    elif sample_format == "json":
        return json.loads(deserialize_sample_format(self.mask)).keys()


labop.SampleMask.get_coordinates = sample_mask_get_coordinates


def sample_array_get_coordinates(self, sample_format=Strings.XARRAY):
    if sample_format == Strings.JSON:
        return self.to_dict(Strings.JSON).values()
    elif sample_format == Strings.XARRAY:
        initial_contents = self.to_data_array()
        return [c for c in initial_contents[Strings.LOCATION].data]
    else:
        raise ValueError(f"Unsupported sample format: {self.sample_format}")


labop.SampleArray.get_coordinates = sample_array_get_coordinates


def sample_array_from_coordinates(
    source: labop.SampleCollection, coordinates: str, sample_type=Strings.XARRAY
):
    mask = labop.SampleMask(source=source)
    mask_array = source.mask(coordinates)
    mask_array.name = mask.identity
    mask.mask = serialize_sample_format(mask_array)
    return mask


labop.SampleArray.from_coordinates = sample_array_from_coordinates


def sample_array_from_container_spec(
    container_type: labop.ContainerSpec, sample_format=Strings.XARRAY
):
    sample_array = labop.SampleArray(container_type=container_type)

    if (
        container_type.queryString
        == "cont:Opentrons24TubeRackwithEppendorf1.5mLSafe-LockSnapcap"
    ):
        geometry = "A1:C8"
    elif container_type.queryString == "cont:StockReagent":
        geometry = "A1"
    else:
        geometry = "A1:H12"

    initial_contents = sample_array.empty(
        geometry=geometry, sample_format=sample_format
    )
    sample_array.initial_contents = serialize_sample_format(initial_contents)
    return sample_array


labop.SampleArray.from_container_spec = sample_array_from_container_spec


def sample_data_empty(self: labop.SampleData, sample_format=Strings.XARRAY):
    if sample_format == "xarray":
        from_samples = self.from_samples.lookup()
        sample_array = from_samples.to_data_array(sample_format=sample_format)
        sample_data = fs.sample_location.where(fs.sample_location.isnull(), nan)
        sample_data.name = self.identity
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
    assert (
        len(table) > 1
    ), "Cannot instantiate SampleData from table with fewer than 2 rows (need header and data)."

    # First row has the column headers
    col_headers = [x["value"] for x in table[0]]
    assert (
        len(col_headers) > 0
    ), "Cannot instantiate SampleData from table with fewer than 1 column (need some data)."
    coord_cols = [
        i for i, x, in enumerate(col_headers) if x in ["Source", "Destination"]
    ]

    coords = {col_headers[i]: [] for i in coord_cols}
    data = []
    for row in table[1:]:
        data.append([x["value"] for i, x in enumerate(row) if i not in coord_cols])
        for i, x in enumerate(row):
            if i in coord_cols:
                coords[col_headers[i]].append(x["value"])
        sample_data = xr.DataArray(data, coords)
        # [nan]*len(masked_array[Strings.SAMPLE]),
        # [ (Strings.SAMPLE, masked_array.coords[Strings.SAMPLE].data) ]

        return sample_data


labop.SampleData.from_table = sample_data_from_table


def activity_node_execution_get_outputs(self):
    return []


labop.ActivityNodeExecution.get_outputs = activity_node_execution_get_outputs


def call_behavior_execution_get_outputs(self):
    return [
        x
        for x in self.call.lookup().parameter_values
        if x.parameter.lookup().property_value.direction == uml.PARAMETER_OUT
    ]


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
        l.warning(
            "Could not import matplotlib.  Install matplotlib to plot SampleArray objects."
        )
        return None


labop.SampleArray.plot = sample_array_plot


def sample_array_sample_coordinates(self, sample_format=Strings.XARRAY, as_list=False):
    sample_array = deserialize_sample_format(self.initial_contents, parent=self)
    if sample_format == Strings.XARRAY:
        if "sort_order" in sample_array:
            sorted = sample_array.sort_order.stack(i=sample_array.sort_order.dims)
            sorted = sorted.where(sorted).dropna("i").sortby("order")
            coords = list(zip(sorted.container.data, sorted.location.data))
            l.warning("Cannot get sample_coordinates() as rectangles when ordered.")
            return coords
        else:
            coords = sample_array.coords[Strings.LOCATION].data.tolist()
            return contiguous_coordinates(coords) if not as_list else coords
        # plate_coords = get_sample_list("A1:H12")
        # if all([c in coords for c in plate_coords]):
        #     return "A1:H12"
        # else:
        #     return coords
    else:
        return sample_array


labop.SampleArray.sample_coordinates = sample_array_sample_coordinates


def sample_mask_sample_coordinates(self, sample_format=Strings.XARRAY, as_list=False):
    sample_array = self.to_masked_data_array()

    if sample_format == Strings.XARRAY:
        coords = sample_array.coords[Strings.LOCATION].data.tolist()
        return contiguous_coordinates(coords) if not as_list else coords
    else:
        return sample_array


labop.SampleMask.sample_coordinates = sample_mask_sample_coordinates


def sample_array_to_dot(self, dot, out_dir="out"):
    name = self.name if (hasattr(self, "name") and self.name) else self.identity
    if self.plot(out_dir=out_dir):
        dot.node(
            name,
            _attributes={
                "label": f'<<table><tr><td><img src="{name}.pdf"></img></td></tr></table>>'
            },
        )
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


def sample_metadata_to_data_array(
    self: labop.SampleMetadata, sample_format=Strings.XARRAY
):
    if not hasattr(self, "descriptions") or self.descriptions is None:
        metadata_array = self.empty(sample_format=sample_format)
    else:
        metadata_array = deserialize_sample_format(self.descriptions, parent=self)
    return metadata_array


labop.SampleMetadata.to_data_array = sample_metadata_to_data_array


def sample_metadata_from_excel(
    filename: Union[str, os.PathLike],
    for_samples: labop.SampleCollection,
    sample_format=Strings.XARRAY,
    record_source=False,
):
    metadata = labop.SampleMetadata(for_samples=for_samples)

    wb = load_workbook(filename=filename, data_only=True)
    sheet_names = wb.get_sheet_names()
    sheet_name = sheet_names[0]
    ws = wb[sheet_name]
    data = ws.values
    cols = next(data)[1:]
    data = list(data)
    idx = [r[0] for r in data]
    data = (islice(r, 1, None) for r in data)
    metadata_df = pd.DataFrame(data, index=idx, columns=cols)
    metadata_df.index.name = Strings.SAMPLE

    if sample_format == Strings.XARRAY:
        # Convert pd.DataFrame into xr.DataArray

        metadata_array = xr.Dataset.from_dataframe(metadata_df)
        if record_source:
            metadata_array = metadata_array.expand_dims(
                {"source": [metadata.identity]}
            )  # Will be replaced when deserilialized by parent.identity
        metadata.descriptions = serialize_sample_format(metadata_array)

        # The metadata_array is now a 2D xr.DataArray with dimensions (sample, metadata)
        # The sample coordinates are sample ids, and the metadata coordinates are metadata attributes
        # The name is the identity of the labop.SampleMetadata holding the metadata_array
    else:
        raise NotImplementedError(
            f"Cannot represent Excel SampleMetadata as sample_format: {sample_format}"
        )

    return metadata


labop.SampleMetadata.from_excel = sample_metadata_from_excel


def sample_mask_container_type(self):
    return self.source.lookup().get_container_type()


labop.SampleMask.get_container_type = sample_mask_container_type


def sample_array_container_type(self):
    return self.container_type


labop.SampleArray.get_container_type = sample_array_container_type


def sample_metadata_for_primitive(
    primitive: labop.Primitive,
    inputs: Dict[str, sbol3.Identified],
    for_samples: labop.SampleCollection,
    sample_format=Strings.XARRAY,
    record_source=False,
):
    metadata = labop.SampleMetadata(for_samples=for_samples)
    # metadata_array = metadata.empty(sample_format=sample_format)

    if sample_format == Strings.XARRAY:
        sample_array = for_samples.to_data_array()

        # Create new metadata for each input to primitive, aside from for_samples
        inputs_meta = {
            k: sample_array.sample_location.where(
                sample_array.sample_location.isnull(), v.identity
            )
            for k, v in inputs.items()
            if v != for_samples
        }

        metadata_dataset = xr.Dataset(inputs_meta, coords=sample_array.coords)
        if record_source:
            metadata_dataset = metadata_dataset.expand_dims(
                {"source": [metadata.identity]}
            )

    elif sample_format == Strings.JSON:
        metadata_dataset = {}
    else:
        raise NotImplementedError(
            f"Cannot represent {primitive} SampleMetadata as sample_format: {sample_format}"
        )

    metadata.descriptions = serialize_sample_format(metadata_dataset)

    return metadata


labop.SampleMetadata.for_primitive = sample_metadata_for_primitive


def dataset_to_dataset(
    self: labop.Dataset, sample_format=Strings.XARRAY, humanize=False
):
    """
    Join the self.data and self.metadata into a single xarray dataset.

    Parameters
    ----------
    self : labop.Dataset
        Dataset comprising data and metadata.
    """
    data = [self.data.to_data_array(sample_format=sample_format)] if self.data else []
    datasets = (
        [d.lookup().to_dataset(sample_format=sample_format) for d in self.dataset]
        if self.dataset
        else []
    )
    metadata = (
        [m.to_data_array(sample_format=sample_format) for m in self.metadata]
        if self.metadata
        else []
    )
    linked_metadata = (
        [
            m.lookup().to_data_array(sample_format=sample_format)
            for m in self.linked_metadata
        ]
        if self.linked_metadata
        else []
    )
    to_merge = data + metadata + datasets + linked_metadata
    ds = xr.merge(to_merge)
    if humanize:
        ds = self.humanize(dataset=ds, sample_format=sample_format)
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
        if Strings.LOCATION in data.coords:
            data = (
                data.assign_coords(
                    samplez=(
                        "location",
                        [
                            (f"{s[:1]}0{s[1:]}" if len(s) == 2 else s)
                            for s in data.coords["location"].data
                        ],
                    )
                )
                .sortby("samplez")
                .reset_coords("samplez", drop=True)
            )
    return data


def sample_data_update_data_sheet(
    self, data_file_path, sheet_name, sample_format=Strings.XARRAY
):
    sample_array = self.humanize(sample_format=sample_format)

    if sample_format == Strings.XARRAY:
        # Check whether data exists in the data template, and load it
        changed = False
        if os.path.exists(data_file_path):
            try:
                data_df = pd.read_excel(data_file_path, sheet_name=sheet_name)
                # Assume that first column is the sample index
                data_df = data_df.set_index(data_df.columns[0])
                if sample_format == Strings.XARRAY:
                    # Convert pd.DataFrame into xr.DataArray
                    sample_data_array = xr.Dataset.from_dataframe(data_df)[
                        sample_array.name
                    ]

                    changed = not (
                        (
                            sample_array.isnull().all()
                            and sample_data_array.isnull().all()
                        )
                        or (sample_data_array == sample_array).all()
                    )
                    if changed:
                        sample_array = sample_data_array
                        self.values = labop.serialize_sample_format(sample_array)

                else:
                    raise Exception(
                        f"Cannot read sample_format {sample_format} from Excel"
                    )
            except Exception as e:
                # Sheet could not be loaded, so it did not change
                pass

        if not changed:
            mode = "a" if os.path.exists(data_file_path) else "w"
            kwargs = {"if_sheet_exists": "replace"} if mode == "a" else {}
            with pd.ExcelWriter(
                data_file_path, mode=mode, engine="openpyxl", **kwargs
            ) as writer:
                sample_array.to_dataframe().to_excel(writer, sheet_name=sheet_name)


labop.SampleData.update_data_sheet = sample_data_update_data_sheet


def dataset_humanize(self, dataset=None, sample_format=Strings.XARRAY):
    # rename all dataset variables to human readible names
    # for variable in dataset.variables:
    #     variable.name = "foo"
    #     for
    # rename all values of variables to human readible values

    if dataset is None:
        dataset = self.to_dataset(
            humanize=True
        )  # to_dataset will call this function again with an xaray.Dataset for dataset

    if sample_format == Strings.XARRAY:
        vars = list(dataset.data_vars.keys())
        var_map = {}
        for var in vars:
            var_obj = self.document.find(var)
            if var_obj is not None:
                var_map[var] = str(var_obj.name)
            values = dataset[var]
            if (
                values.dtype.str == "<U102"
                or values.dtype.str == "|O"
                or values.dtype.str == "<U95"
            ):
                # unique_values = set(
                #     values.stack(i=values.coords._names)
                #     .dropna("i")
                #     .data.tolist()
                # )
                unique_values = np.unique(dataset[var].data).tolist()
                for old in unique_values:
                    val_obj = self.document.find(old)
                    if val_obj is not None:
                        new = str(val_obj)
                        values = values.astype("str").str.replace(old, str(new))
                dataset = dataset.assign({var: values})

        dataset = dataset.rename(var_map)
        for c in dataset.coords._names:
            unique_values = np.unique(dataset[c].data).tolist()
            for old in unique_values:
                val_obj = self.document.find(old)
                if val_obj is not None:
                    new = str(val_obj)
                    dataset[c] = dataset[c].str.replace(old, str(new))
        return dataset
    else:
        return dataset


labop.Dataset.humanize = dataset_humanize


def sample_data_humanize(self, sample_format=Strings.XARRAY):
    # rename all dataset variables to human readible names
    # for variable in dataset.variables:
    #     variable.name = "foo"
    #     for
    # rename all values of variables to human readible values
    sample_array = self.to_data_array(sample_format=sample_format)
    if sample_format == Strings.XARRAY:
        var = sample_array.name
        var_obj = self.document.find(var)
        if var_obj is not None:
            sample_array.name = str(var_obj.name)

        # humanize the data
        if sample_array.dtype.str == "<U102" or sample_array.dtype.str == "|O":
            unique_values = set(sample_array.data.tolist())
            for old in unique_values:
                val_obj = self.document.find(old)
                if val_obj is not None:
                    new = str(val_obj)
                    sample_array = sample_array.str.replace(old, str(new))
        for c in sample_array.coords:
            unique_values = set(sample_array[c].data.tolist())
            for old in unique_values:
                val_obj = self.document.find(old)
                if val_obj is not None:
                    new = str(val_obj)
                    sample_array[c] = sample_array[c].str.replace(old, str(new))
        return sample_array
    else:
        return sample_array


labop.SampleData.humanize = sample_data_humanize


def dataset_update_data_sheet(
    self, data_file_path, sheet_name, sample_format=Strings.XARRAY
):
    dataset = sort_samples(self.to_dataset(humanize=True), sample_format=sample_format)

    if len(dataset) > 0:
        mode = "a" if os.path.exists(data_file_path) else "w"
        kwargs = {"if_sheet_exists": "replace"} if mode == "a" else {}
        with pd.ExcelWriter(
            data_file_path, mode=mode, engine="openpyxl", **kwargs
        ) as writer:
            drop_list = [x for x in ["reagent", "sample", "node"] if x in dataset]
            if "contents" in dataset:
                contents_df = (
                    dataset.contents.to_dataset("reagent")
                    .to_dataframe()
                    .reset_index()
                    .set_index(["container", "location"])
                )
                drop_list += ["contents"]
            else:
                contents_df = None
            if "sample_location" in dataset:
                sample_df = (
                    dataset.sample_location.to_dataset()
                    .to_dataframe()
                    .reset_index()
                    .set_index(["container", "location"])
                )
                drop_list += ["sample_location"]
            else:
                sample_df = None
            meta_df = (
                dataset.drop(drop_list)
                .to_dataframe()
                .reset_index()
                .set_index(["container", "location"])
            )
            all_df = (
                meta_df.join(
                    (
                        contents_df.join(
                            sample_df, lsuffix="_contents", rsuffix="_sample"
                        )
                        if sample_df is not None
                        else contents_df
                    ),
                    lsuffix="meta",
                )
                if contents_df is not None
                else meta_df
            )
            all_df.to_excel(writer, sheet_name=sheet_name)
            # if Strings.CONTENTS in dataset:
            #     dataset.contents.to_dataset(
            #         Strings.REAGENT
            #     ).to_dataframe().reset_index().to_excel(
            #         writer, sheet_name=sheet_name
            #     )
            # else:
            #     dataset.to_array().transpose("container", "location", ...).drop(
            #         ["reagent", "sample"]
            #     ).to_dataset(
            #         "variable", "contents"
            #     ).to_dataframe().reset_index().to_excel(
            #         writer, sheet_name=sheet_name
            #     )


labop.Dataset.update_data_sheet = dataset_update_data_sheet


def sample_metadata_from_sample_graph(for_samples, engine, record_source=False):
    metadata = labop.SampleMetadata(for_samples=for_samples)

    if engine.sample_format == Strings.XARRAY:
        # Convert pd.DataFrame into xr.DataArray
        samples = for_samples.to_data_array()

        # Get most current sample in each container/location apppearing in samples
        metadata_array = engine.prov_observer.select_samples_from_graph(
            samples
        ).reset_coords(drop=True)
        if record_source:
            metadata_array = metadata_array.expand_dims(
                {"source": [metadata.identity]}
            )  # Will be replaced when deserilialized by parent.identity
        metadata.descriptions = serialize_sample_format(metadata_array)

        # The metadata_array is now a 2D xr.DataArray with dimensions (sample, metadata)
        # The sample coordinates are sample ids, and the metadata coordinates are metadata attributes
        # The name is the identity of the labop.SampleMetadata holding the metadata_array
    else:
        raise NotImplementedError(
            f"Cannot represent Excel SampleMetadata as sample_format: {sample_format}"
        )

    return metadata


labop.SampleMetadata.from_sample_graph = sample_metadata_from_sample_graph
