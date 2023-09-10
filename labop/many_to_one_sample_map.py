"""
The ManyToOneSampleMap class defines the functions corresponding to the dynamically generated labop class ManyToOneSampleMap
"""

import xarray as xr

import labop.inner as inner
from labop.sample_map import SampleMap


class ManyToOneSampleMap(inner.ManyToOneSampleMap, SampleMap):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_map(self):
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
