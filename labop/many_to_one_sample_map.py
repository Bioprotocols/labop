"""
The ManyToOneSampleMap class defines the functions corresponding to the dynamically generated labop class ManyToOneSampleMap
"""

import labop.inner as inner
from labop.sample_map import SampleMap


class ManyToOneSampleMap(inner.ManyToOneSampleMap, SampleMap):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
