"""
The Dataset class defines the functions corresponding to the dynamically generated labop class Dataset
"""

import os

import pandas as pd
import xarray as xr

import labop.inner as inner

from .data import sort_samples
from .strings import Strings


class Dataset(inner.Dataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_dataset(self, sample_format=Strings.XARRAY, humanize=False):
        """
        Join the self.data and self.metadata into a single xarray dataset.

        Parameters
        ----------
        self : labop.Dataset
            Dataset comprising data and metadata.
        """
        data = (
            [self.data.to_data_array(sample_format=sample_format)] if self.data else []
        )
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

    def humanize(self, dataset=None, sample_format=Strings.XARRAY):
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
                    unique_values = np.unique(
                        dataset[var].dropna(dim=Strings.LOCATION).data
                    ).tolist()
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

    def update_data_sheet(
        self, data_file_path, sheet_name, sample_format=Strings.XARRAY
    ):
        dataset = sort_samples(
            self.to_dataset(humanize=True), sample_format=sample_format
        )

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
                                sample_df,
                                lsuffix="_contents",
                                rsuffix="_sample",
                            )
                            if sample_df is not None
                            else contents_df
                        ),
                        lsuffix="meta",
                    )
                    if contents_df is not None
                    else meta_df
                )
                all_df.reset_index().to_excel(writer, sheet_name=sheet_name)
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
