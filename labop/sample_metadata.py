"""
The SampleMetadata class defines the functions corresponding to the dynamically generated labop class SampleMetadata
"""

import os
from itertools import islice
from typing import Dict, Union

import pandas as pd
import sbol3
import xarray as xr
from openpyxl import load_workbook

import labop.inner as inner
from labop.data import deserialize_sample_format, serialize_sample_format
from labop.sample_collection import SampleCollection
from labop.strings import Strings
from uml.behavior import Behavior


class SampleMetadata(inner.SampleMetadata):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def empty(self, sample_format=Strings.XARRAY):
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

    def to_data_array(self, sample_format=Strings.XARRAY):
        if not hasattr(self, "descriptions") or self.descriptions is None:
            metadata_array = self.empty(sample_format=sample_format)
        else:
            metadata_array = deserialize_sample_format(self.descriptions, parent=self)
        return metadata_array

    def from_excel(
        filename: Union[str, os.PathLike],
        for_samples: SampleCollection,
        sample_format=Strings.XARRAY,
        record_source=False,
    ):
        metadata = SampleMetadata(for_samples=for_samples)

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

    def for_primitive(
        primitive: Behavior,
        inputs: Dict[str, sbol3.Identified],
        for_samples: SampleCollection,
        sample_format=Strings.XARRAY,
        record_source=False,
    ):
        metadata = SampleMetadata(for_samples=for_samples)
        # metadata_array = metadata.empty(sample_format=sample_format)

        if sample_format == Strings.XARRAY:
            sample_array = for_samples.to_data_array()

            # Create new metadata for each input to primitive, aside from for_samples
            inputs_meta = {
                k: xr.DataArray(
                    [v.identity] * len(sample_array.coords[Strings.SAMPLE]),
                    dims=Strings.SAMPLE,
                    coords={Strings.SAMPLE: sample_array.coords[Strings.SAMPLE]},
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

    def to_dataarray(self):
        return deserialize_sample_format(self.descriptions, parent=self)
