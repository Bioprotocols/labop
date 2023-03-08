import random
import json
from urllib.parse import quote, unquote

import xarray as xr

from labop.strings import Strings


class LabInterface():

    @staticmethod
    def measure_absorbance(coordinates: list[str], wavelength: float, sample_format: str) -> xr.DataArray:
        # Override this method to interface with laboratory plate reader API
        if sample_format == Strings.XARRAY:
            measurements = xr.DataArray(
                [random.random() for c in coordinates],
                name=Strings.DATA,
                dims=(Strings.SAMPLE),
                coords={Strings.SAMPLE: coordinates}
                )
            measurements = quote(json.dumps(measurements.to_dict()))
        elif sample_format == Strings.JSON:
            measurements = quote(json.dumps({}))
        else:
            raise Exception(f"Cannot initialize contents of sample_format: {sample_format}")
        return measurements

    @staticmethod
    def measure_fluorescence(coordinates: list[str], excitation: float, emission: float, bandpass: float, sample_format: str) -> xr.DataArray:
        # Override this method to interface with laboratory plate reader API
        if sample_format == Strings.XARRAY:
            measurements = xr.DataArray(
                [random.random() for c in coordinates],
                name=Strings.DATA,
                dims=(Strings.SAMPLE),
                coords={Strings.SAMPLE: coordinates}
                )
            measurements = quote(json.dumps(measurements.to_dict()))
        elif sample_format == Strings.JSON:
            measurements = quote(json.dumps({}))
        else:
            raise Exception(f"Cannot initialize contents of sample_format: {sample_format}")
        return measurements

    @staticmethod
    def check_lims_inventory(self, matching_containers: list) -> str:
        # Override this method to interface with laboratory lims system
        return matching_containers[0]
