"""
Quadrant names for the Star Trek game.
Original names from the 1978 BASIC version.
"""

# 8x8 grid of quadrant names (row, column)
QUADRANT_NAMES = [
    # Row 0
    ["ANTARES", "RIGEL", "PROCYON", "VEGA", "CANOPUS", "ALTAIR", "SAGITTARIUS", "POLLUX"],
    # Row 1
    ["SIRIUS", "DENEB", "CAPELLA", "BETELGEUSE", "ALDEBARAN", "REGULUS", "ARCTURUS", "SPICA"],
    # Row 2
    ["POLARIS", "GACRUX", "HADAR", "MIMOSA", "ACRUX", "SHAULA", "BELLATRIX", "ELNATH"],
    # Row 3
    ["ALNILAM", "ALNITAK", "SAIPH", "CASTOR", "MIZAR", "ALCOR", "HAMAL", "DENEBOLA"],
    # Row 4
    ["ALPHECCA", "RASALHAGUE", "KOCHAB", "PHERKAD", "MENKENT", "ALBIREO", "GIENAH", "ALUDRA"],
    # Row 5
    ["SCHEDAR", "CAPH", "RUCHBAH", "SEGIN", "ACHIRD", "ALMACH", "MIRACH", "ALGOL"],
    # Row 6
    ["ATLAS", "ELECTRA", "MAIA", "MEROPE", "TAYGETA", "CELAENO", "ALCYONE", "PLEIONE"],
    # Row 7
    ["ALPHARD", "SUHAIL", "NAOS", "REGOR", "ALSUHAIL", "MARKEB", "AVIOR", "MIAPLACIDUS"],
]

# Suffixes for quadrant names (I, II, III, IV)
QUADRANT_SUFFIXES = ["I", "II", "III", "IV"]


def get_quadrant_name(row: int, col: int) -> str:
    """Get the name of a quadrant at the given coordinates."""
    if 0 <= row < 8 and 0 <= col < 8:
        base_name = QUADRANT_NAMES[row][col]
        suffix = QUADRANT_SUFFIXES[(row + col) % 4]
        return f"{base_name} {suffix}"
    return "UNKNOWN"
