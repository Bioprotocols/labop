"""
This is a utility specifically for use with iGEM protocols.  It post-processes markdown to create a table for the Materials Section that indicates where each iGEM part is located in the distribution kit
"""

import sbol3

import labop


def render_kit_coordinates_table(ex: labop.ProtocolExecution):
    # Get iGEM parts from Document
    components = [
        c
        for c in ex.document.objects
        if type(c) is sbol3.Component and "igem" in c.types[0]
    ]

    # Extract kit coordinates from description, assuming description has the following
    # format: 'BBa_I20270 Kit Plate 1 Well 1A'
    components = [
        (
            c.description.split(" ")[0],  # Part ID
            " ".join(c.description.split(" ")[1:]),
        )  # Kit coordinates
        for c in components
    ]

    # Format markdown table
    table = (
        "#### Table 1: Part Locations in Distribution Kit\n"
        "| Part | Coordinate |\n"
        "| ---- | -------------- |\n"
    )
    for part, coordinate in components:
        table += f"|{part}|{coordinate}|\n"
    table += "\n\n"

    # Insert into markdown document immediately before the Protocol Steps section
    insert_index = ex.markdown.find("## Protocol Steps")
    ex.markdown = ex.markdown[:insert_index] + table + ex.markdown[insert_index:]
