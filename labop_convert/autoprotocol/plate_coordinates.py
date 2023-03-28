"""
Autoprotocol specific extensions for Autoprotocol containers
"""

from autoprotocol.container import Container, WellGroup

from labop_convert.plate_coordinates import coordinate_rect_to_row_col_pairs


def coordinate_rect_to_well_group(container: Container, coordinates: str):
    indices = coordinate_rect_to_row_col_pairs(coordinates)
    wells = []

    try:
        for i, j in indices:
            well = container.well_from_coordinates(i, j)
            wells.append(well)
        # wells = [container.well_from_coordinates(i, j) for i, j in indices]
    except Exception as e:
        print(container.container_type)
        print(i, j)
        print(container.to_dict())
        raise e
    return WellGroup(wells)
