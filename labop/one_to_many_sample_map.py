"""
The OneToManySampleMap class defines the functions corresponding to the dynamically generated labop class OneToManySampleMap
"""

import xarray as xr

import labop.inner as inner
from labop.sample_map import SampleMap


class OneToManySampleMap(inner.OneToManySampleMap, SampleMap):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_map(self):
        """
        Get the XArray Dataset from the values field.
        """
        if not hasattr(self, "values") or not self.values:
            source = self.sources
            targets = self.targets

            aliquots = get_sample_list(
                geometry="A1:H12"
            )  # FIXME need to use the spec for each source and target
            source_to_target_arrays = {
                target.identity: xr.DataArray(
                    [""] * len(aliquots),
                    dims=(source.identity),
                    coords={source.identity: aliquots},
                )
                for target in targets
            }

            sample_map = xr.Dataset(source_to_target_arrays)
        else:
            sample_map = labop.SampleMap.get_map()
        return sample_map
