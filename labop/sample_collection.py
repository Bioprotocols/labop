"""
The SampleCollection class defines the functions corresponding to the dynamically generated labop class SampleCollection
"""

import labop.inner as inner


class SampleCollection(inner.SampleCollection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
