"""
The SampleMap class defines the functions corresponding to the dynamically generated labop class SampleMap
"""

import labop.inner as inner
from labop.data import deserialize_sample_format, serialize_sample_format


class SampleMap(inner.SampleMap):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self):
        """
        Render the sample map using a matplotlib plot
        """
        self.plot()

    def get_map(self):
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

    def set_map(self, sample_map):
        """
        Set the XArray Dataset to the values field.
        """
        self.values = serialize_sample_format(sample_map)
