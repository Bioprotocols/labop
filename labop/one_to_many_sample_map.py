"""
The OneToManySampleMap class defines the functions corresponding to the dynamically generated labop class OneToManySampleMap
"""

import labop.inner as inner
from labop.sample_map import SampleMap


class OneToManySampleMap(inner.OneToManySampleMap, SampleMap):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
