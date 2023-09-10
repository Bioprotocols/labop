"""
The SampleData class defines the functions corresponding to the dynamically generated labop class SampleData
"""

import os
from typing import Dict, List

import pandas as pd
import xarray as xr
from numpy import nan

import labop.inner as inner
from labop.data import deserialize_sample_format, serialize_sample_format
from labop.strings import Strings


class SampleData(inner.SampleData):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def empty(self, sample_format=Strings.XARRAY):
        if sample_format == "xarray":
            from_samples = self.from_samples.lookup()
            sample_array = from_samples.to_data_array(sample_format=sample_format)
            sample_data = fs.sample_location.where(fs.sample_location.isnull(), nan)
            sample_data.name = self.identity
            self.values = serialize_sample_format(sample_data)
        else:
            raise NotImplementedError()
        return sample_data

    def to_data_array(self, sample_format=Strings.XARRAY):
        if not hasattr(self, "values") or self.values is None:
            sample_data = self.empty(sample_format=sample_format)
        else:
            sample_data = deserialize_sample_format(self.values, parent=self)
        return sample_data

    def from_table(self, table: List[List[Dict[str, str]]]):
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

    def update_data_sheet(
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
                    data_df = data_df.set_index([Strings.CONTAINER, Strings.LOCATION])
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
                            # reverse humanized coordinates
                            sample_data_array = sample_data_array.assign_coords(
                                self.to_data_array().coords
                            )
                            sample_array = sample_data_array
                            self.values = serialize_sample_format(sample_array)

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
                    sample_array.to_dataframe().reset_index().to_excel(
                        writer, sheet_name=sheet_name
                    )

    def humanize(self, sample_format=Strings.XARRAY):
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

    def __str__(self):
        """
        Create a human readable string for a SampleData.
        :param self:
        :return: str
        """
        return f"SampleData(name={self.name}, from_samples={self.from_samples}, values={self.values})"
