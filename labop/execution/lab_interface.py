import json
from urllib.parse import quote

import xarray as xr
from numpy import nan

from ..data import serialize_sample_format
from ..strings import Strings


class LabInterface:
    @staticmethod
    def measure_absorbance(
        samples: "SampleCollection", wavelength: float, sample_format: str
    ) -> xr.DataArray:
        # Override this method to interface with laboratory plate reader API
        if sample_format == Strings.XARRAY:
            s = samples.to_data_array()
            measurements = s.sample_location.where(s.sample_location.isnull(), nan)
            measurements = serialize_sample_format(measurements)
        elif sample_format == Strings.JSON:
            measurements = quote(json.dumps({}))
        else:
            raise Exception(
                f"Cannot initialize contents of sample_format: {sample_format}"
            )
        return measurements

    @staticmethod
    def measure_fluorescence(
        samples: "SampleCollection",
        excitation: float,
        emission: float,
        bandpass: float,
        sample_format: str,
    ) -> xr.DataArray:
        # Override this method to interface with laboratory plate reader API
        if sample_format == Strings.XARRAY:
            s = samples.to_data_array()
            measurements = s.sample_location.where(s.sample_location.isnull(), nan)
            measurements = serialize_sample_format(measurements)
        elif sample_format == Strings.JSON:
            measurements = quote(json.dumps({}))
        else:
            raise Exception(
                f"Cannot initialize contents of sample_format: {sample_format}"
            )
        return measurements

    @staticmethod
    def check_lims_inventory(self, matching_containers: list) -> str:
        # Override this method to interface with laboratory lims system
        return matching_containers[0]
