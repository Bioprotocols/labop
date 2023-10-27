"""
Generic helper functions for dealing with plate coordinates
"""

import re
from string import ascii_letters

import numpy as np

from labop.strings import Strings


def get_sample_list(geometry="A1:H12"):
    rects = geometry.split(",")
    row_col_pairs = []
    for rect in rects:
        row_col_pairs += coordinate_rect_to_row_col_pairs(rect)
    aliquots = [f"{num2row(r+1)}{c+1}" for (r, c) in row_col_pairs]
    return aliquots


def contiguous_coordinates(coords):
    """
    Summarize a list of well coordinates of the form ["A1", "A2", ...] with a rectangle of the form "A1:B2".  Ensure that the elements of the list are a rectangle without any missing wells.

    Parameters
    ----------
    coords : List[str]
        List of coordinates to summarize.

    Returns
    -------
    Union[List[str], str]
        The original list (if not a rectangle) or a summarized rectangle string.
    """
    # assumes that coords are sorted
    if len(coords) == 0:
        return ""
    elif len(coords) == 1:
        return coords[0]
    else:
        pairs = roboticize_2D(coords)
        min_row = min([row for (row, _) in pairs])
        max_row = max([row for (row, _) in pairs])
        min_col = min([col for (_, col) in pairs])
        max_col = max([col for (_, col) in pairs])
        col_range = range(min_col, max_col + 1)
        row_range = range(min_row, max_row + 1)
        entries = np.array([[(x, y) in pairs for y in col_range] for x in row_range])
        if all(
            [
                all([entries[x - min_row][y - min_col] for y in col_range])
                for x in row_range
            ]
        ):
            return f"{coords[0]}:{coords[-1]}"
        else:
            return coords


def roboticize_2D(coords):
    """
    Convert a list strings or string representation of coordinates to a list of pairs of integers.  For example convert ["A1", "A2", ...] to [(0, 0), (0, 1), ...].  Similarly also convert rectangle coordinates of the form "A1:B12" to a list of pairs of integers.

    Parameters
    ----------
    coords : Union[List[str], str]
        Humanized coordinates

    Returns
    -------
    List[Tuple[int, int]]
        roboicized coordinates
    """
    if isinstance(coords, list):
        return [y for x in coords for y in roboticize_2D(x)]
    else:
        pairs = coordinate_rect_to_row_col_pairs(coords)
        return pairs


def num2row(num: int):
    """
    Get the alpha column string from the index.
    - 1 -> A
    - 26 -> Z
    - 27 -> AA
    - 52 -> AZ
    - etc
    """
    if num < 1:
        raise ValueError("Cannot convert num to column, num is too small.")
    col = ""
    while True:
        if num > 26:
            num, r = divmod(num - 1, 26)
            col = chr(r + ord("A")) + col
        else:
            return chr(num + ord("A") - 1) + col


def row2num(col: str):
    """
    Get the index of the alpha column string.
    - A -> 1
    - Z -> 26
    - AA -> 27
    - AZ -> 52
    - etc
    """
    num = 0
    for c in col:
        if c in ascii_letters:
            num = num * 26 + (ord(c.upper()) - ord("A")) + 1
        else:
            raise Exception(f"Invalid character: {c}")
    return num


def coordinate_to_row_col(coord: str):
    m = re.match("^([a-zA-Z]+)([0-9]+)$", coord)
    if m is None:
        raise Exception(f"Invalid coordinate: {coord}")
    # convert column to index and then adjust to zero-based indices
    return (row2num(m.group(1)) - 1), (int(m.group(2)) - 1)


def coordinate_rect_to_row_col_pairs(coords: str) -> list:
    num_separators = coords.count(":")
    if num_separators == 0:
        return [coordinate_to_row_col(coords)]
    elif num_separators == 1:
        parts = coords.split(":")
        frow, fcol = coordinate_to_row_col(parts[0])
        srow, scol = coordinate_to_row_col(parts[1])
        indices = []
        for i in range(fcol, scol + 1):
            for j in range(frow, srow + 1):
                indices.append((j, i))
        return indices
    raise Exception(f"Invalid coordinates: {coords}")


def flatten_coordinates(coords: str, direction=Strings.ROW_DIRECTION):
    """
    Convert a list strings, e.g. ["A1", "A2", ...]  or string representation of coordinate rectange, e.g., "A1:H12"  to a list of flat indices, e.g., (1, 2, ..., 96).

    Parameters
    ----------
    coords : Union[List[str], str]
        Humanized coordinates

    Returns
    -------
    List
        well coordinates converted to flat indices
    """

    pairs = roboticize_2D(coords)
    if direction == Strings.ROW_DIRECTION:
        return [i_row * 12 + i_col + 1 for i_row, i_col in pairs]
    elif direction == Strings.COLUMN_DIRECTION:
        return [i_col * 8 + i_row + 1 for i_row, i_col in pairs]
    else:
        raise Exception(
            f"Don't know how to flatten coordinates in the direction: {direction}."
        )
