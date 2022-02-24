"""
Functions related to data i/o in connection with a protocol execution trace.

This file monkey-patches the imported paml classes with data handling functions.
"""

import pandas as pd
import paml_convert
import re
from paml_convert.plate_coordinates import coordinate_rect_to_row_col_pairs, num2col
from paml import SampleMask, SampleData, SampleArray
from io import StringIO

import logging
l = logging.getLogger(__file__)
l.setLevel(logging.ERROR)

def sample_array_to_dataframe(self):
    container_type = self.container_type.lookup()
    contents = self.contents

    # FIXME need to find a definition of the container topology from the type

    # FIXME this assumes a 96 well plate
    l.warn("Warning: Assuming that the SampleArray is a 96 well microplate!")

    row_col_pairs = coordinate_rect_to_row_col_pairs("A1:H12")
    aliquots = [f"{num2col(c+1)}{r}" for (r, c) in row_col_pairs]
    sources = [self.name for i in range(len(aliquots))]
    df = pd.DataFrame({
        "aliquot" : aliquots,
        "source" : sources})
    return df
SampleArray.to_dataframe = sample_array_to_dataframe

def sample_mask_to_dataframe(self):
    source = self.source.lookup()
    mask = self.mask
    m = re.match('^([a-zA-Z])([0-9]+):([a-zA-Z])([0-9]+)$', self.mask)
    if m is None:
        raise Exception(f"Invalid mask: {mask}")

    row_col_pairs = coordinate_rect_to_row_col_pairs(mask)
    aliquots = [f"{num2col(c+1)}{r}" for (r, c) in row_col_pairs]
    sources = [source.name for i in range(len(aliquots))]
    df = pd.DataFrame({
        "aliquot" : aliquots,
        "source" : sources})
    return df
SampleMask.to_dataframe = sample_mask_to_dataframe

def sample_data_to_dataframe(self):
    if not hasattr(self, "values") or \
       not self.values:
        from_samples = self.from_samples.lookup()
        df = from_samples.to_dataframe()
        df['values'] = ""
    else:
        df = pd.read_csv(self.values, index_col=0)

    return df
SampleData.to_dataframe = sample_data_to_dataframe

def sample_data_from_dataframe(self, df, df_file):
    data = df.to_csv()
    self.values = df_file
    df.to_csv(self.values)
SampleData.from_dataframe = sample_data_from_dataframe
