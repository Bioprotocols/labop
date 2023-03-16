"""
The SampleMap class defines the functions corresponding to the dynamically generated labop class SampleMap
"""

import labop.inner as inner


class SampleMap(inner.SampleMap):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self):
        """
        Render the sample map using a matplotlib plot
        """
        self.plot()
