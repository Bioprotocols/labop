"""
Autoprotocol specific extensions for Autoprotocol containers
"""

from autoprotocol.container import Container, WellGroup

from labop_convert.plate_coordinates import coordinate_rect_to_row_col_pairs


def coordinate_rect_to_well_group(container: Container, coordinates: str):
    indices = coordinate_rect_to_row_col_pairs(coordinates)
    wells = [container.well_from_coordinates(i, j) for i, j in indices]
    return WellGroup(wells)
