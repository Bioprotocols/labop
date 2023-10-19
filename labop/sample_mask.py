"""
The SampleMask class defines the functions corresponding to the dynamically generated labop class SampleMask
"""

import json

import xarray as xr

from . import inner
from .data import deserialize_sample_format, serialize_sample_format
from .sample_collection import SampleCollection
from .strings import Strings
from .utils.plate_coordinates import contiguous_coordinates


class SampleMask(inner.SampleMask, SampleCollection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_source(self):
        return self.source.lookup()

    def new_sample_id(self) -> str:
        return self.source.lookup().new_sample_id()

    def empty(self, sample_format=Strings.XARRAY):
        if sample_format == "xarray":
            source_samples = self.get_source()
            sample_array = source_samples.to_data_array(sample_format=sample_format)
            mask_array = xr.DataArray(
                [True] * len(sample_array[Strings.SAMPLE]),
                name=self.identity,
                dims=(Strings.SAMPLE),
                coords={Strings.SAMPLE: sample_array.coords[Strings.SAMPLE].data},
            )
            self.mask = serialize_sample_format(mask_array)
        else:
            raise NotImplementedError()
        return mask_array

    def to_data_array(self, sample_format=Strings.XARRAY, order=Strings.ROW_DIRECTION):
        if not hasattr(self, "mask") or self.mask is None:
            sample_mask = self.empty(sample_format=sample_format)
        else:
            sample_mask = deserialize_sample_format(self.mask, parent=self, order=order)
        return sample_mask

    def to_masked_data_array(self, sample_format=Strings.XARRAY):
        source = self.get_source()
        masked_array = source.mask(self)
        return masked_array

    def from_coordinates(
        source: SampleCollection,
        coordinates: str,
        sample_format=Strings.XARRAY,
    ):
        mask = SampleMask(source=source)
        mask_array = source.mask(coordinates, sample_format=sample_format)
        mask.mask = serialize_sample_format(mask_array)
        return mask

    def get_coordinates(self, sample_format=Strings.XARRAY):
        if sample_format == "xarray":
            mask = self.to_data_array()
            return mask.location.data.tolist()
        elif sample_format == "json":
            return json.loads(deserialize_sample_format(self.mask)).keys()

    def sample_coordinates(self, sample_format=Strings.XARRAY, as_list=False):
        sample_array = self.to_masked_data_array()

        if sample_format == Strings.XARRAY:
            coords = sample_array.coords[Strings.LOCATION].data.tolist()
            return contiguous_coordinates(coords) if not as_list else coords
        else:
            return sample_array

    def to_dot(self, dot, out_dir="out"):
        name = self.name if (hasattr(self, "name") and self.name) else self.identity
        if self.plot(out_dir=out_dir):
            dot.node(
                name,
                _attributes={
                    "label": f'<<table><tr><td><img src="{name}.pdf"></img></td></tr></table>>'
                },
            )
            return name
        else:
            dot.node(name)
            return name

    def __str__(self):
        """
        Create a human readable string for a SampleMask.
        :param self:
        :return: str
        """
        return f"SampleMask(name={self.name}, source={self.source}, mask={self.mask})"

    def get_container_type(self):
        return self.get_source().get_container_type()


if __name__ == "__main__":
    import doctest

    doctest.testmod(
        # extraglobs={"my_literal_specification": LiteralSpecification()}
    )
