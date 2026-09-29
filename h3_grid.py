import h3

# Uttarakhand bounding box:
# Min Lon: ~77.56, Max Lon: ~81.03
# Min Lat: ~28.72, Max Lat: ~31.47
WEST = 77.5
EAST = 81.1
SOUTH = 28.7
NORTH = 31.5

H3_RESOLUTION = 6


def get_uttarakhand_cells(resolution: int = H3_RESOLUTION):
    """
    Generate H3 cells covering the Uttarakhand bounding box.
    Actual district/state boundary clipping is handled in main.py.
    """
    uk_bbox = h3.LatLngPoly([
        (SOUTH, WEST),
        (SOUTH, EAST),
        (NORTH, EAST),
        (NORTH, WEST),
    ])

    return h3.h3shape_to_cells(
        uk_bbox,
        resolution,
    )


def get_ner_cells():
    """Backwards-compatible alias for primary cell generation."""
    return get_uttarakhand_cells()


def get_cell_info(cell):
    """
    Convert an H3 cell into useful geographic information.
    """

    lat, lon = h3.cell_to_latlng(cell)

    boundary = h3.cell_to_boundary(cell)

    # H3 gives:
    # [(lat, lon), ...]
    #
    # GeoJSON uses:
    # [(lon, lat), ...]

    boundary = [
        [lon, lat]
        for lat, lon in boundary
    ]

    return {
        "h3": cell,
        "lat": lat,
        "lon": lon,
        "boundary": boundary,
    }
