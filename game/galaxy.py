"""
Galaxy, Quadrant, and Sector data structures for Star Trek game.
"""

import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum

from data.quadrant_names import get_quadrant_name


class EntityType(Enum):
    """Types of entities in a sector."""
    EMPTY = 0
    ENTERPRISE = 1
    KLINGON = 2
    STARBASE = 3
    STAR = 4


@dataclass
class Klingon:
    """Represents a Klingon ship."""
    sector_row: int
    sector_col: int
    energy: int = 0

    def __post_init__(self):
        if self.energy == 0:
            # Random energy between 300 and 599 (original BASIC formula)
            self.energy = 300 + random.randint(0, 299)


@dataclass
class Quadrant:
    """
    Represents an 8x8 quadrant in the galaxy.
    Contains information about Klingons, starbases, and stars.
    """
    row: int
    col: int
    klingons: int = 0
    starbases: int = 0
    stars: int = 0
    scanned: bool = False

    # Detailed sector map (populated when Enterprise enters)
    sector_map: List[List[EntityType]] = field(default_factory=list)
    klingon_ships: List[Klingon] = field(default_factory=list)
    starbase_pos: Optional[Tuple[int, int]] = None
    star_positions: List[Tuple[int, int]] = field(default_factory=list)

    @property
    def name(self) -> str:
        """Get the name of this quadrant."""
        return get_quadrant_name(self.row, self.col)

    def get_lrs_value(self) -> int:
        """Get the 3-digit LRS value (KBS format)."""
        return self.klingons * 100 + self.starbases * 10 + self.stars

    def initialize_sector_map(self) -> None:
        """Initialize the 8x8 sector map with entities."""
        # Create empty map
        self.sector_map = [[EntityType.EMPTY for _ in range(8)] for _ in range(8)]
        self.klingon_ships.clear()
        self.star_positions.clear()
        self.starbase_pos = None

        # Place Klingons
        for _ in range(self.klingons):
            row, col = self._find_empty_sector()
            self.sector_map[row][col] = EntityType.KLINGON
            self.klingon_ships.append(Klingon(row, col))

        # Place starbase
        if self.starbases > 0:
            row, col = self._find_empty_sector()
            self.sector_map[row][col] = EntityType.STARBASE
            self.starbase_pos = (row, col)

        # Place stars
        for _ in range(self.stars):
            row, col = self._find_empty_sector()
            self.sector_map[row][col] = EntityType.STAR
            self.star_positions.append((row, col))

    def _find_empty_sector(self) -> Tuple[int, int]:
        """Find a random empty sector."""
        while True:
            row = random.randint(0, 7)
            col = random.randint(0, 7)
            if self.sector_map[row][col] == EntityType.EMPTY:
                return row, col

    def place_enterprise(self, row: int, col: int) -> Tuple[int, int]:
        """
        Place the Enterprise in the quadrant.
        If the specified position is occupied, find a nearby empty sector.
        Returns the actual position where Enterprise was placed.
        """
        if not self.sector_map:
            self.initialize_sector_map()

        # If position is occupied, find empty sector
        if self.sector_map[row][col] != EntityType.EMPTY:
            row, col = self._find_empty_sector()

        self.sector_map[row][col] = EntityType.ENTERPRISE
        return row, col

    def remove_enterprise(self, row: int, col: int) -> None:
        """Remove the Enterprise from its current position."""
        if self.sector_map and 0 <= row < 8 and 0 <= col < 8:
            if self.sector_map[row][col] == EntityType.ENTERPRISE:
                self.sector_map[row][col] = EntityType.EMPTY

    def remove_klingon(self, row: int, col: int) -> bool:
        """
        Remove a Klingon from the specified position.
        Returns True if a Klingon was removed.
        """
        if self.sector_map[row][col] == EntityType.KLINGON:
            self.sector_map[row][col] = EntityType.EMPTY
            # Remove from klingon_ships list
            self.klingon_ships = [k for k in self.klingon_ships
                                   if not (k.sector_row == row and k.sector_col == col)]
            self.klingons -= 1
            return True
        return False

    def get_entity_at(self, row: int, col: int) -> EntityType:
        """Get the entity type at a specific sector."""
        if self.sector_map and 0 <= row < 8 and 0 <= col < 8:
            return self.sector_map[row][col]
        return EntityType.EMPTY

    def is_adjacent_to_starbase(self, row: int, col: int) -> bool:
        """Check if the given position is adjacent to a starbase."""
        if self.starbase_pos is None:
            return False

        sb_row, sb_col = self.starbase_pos
        return abs(row - sb_row) <= 1 and abs(col - sb_col) <= 1


class Galaxy:
    """
    Represents the 8x8 galaxy containing all quadrants.
    """

    def __init__(self):
        self.quadrants: List[List[Quadrant]] = []
        self.total_klingons = 0
        self.total_starbases = 0
        self.initial_klingons = 0
        self.stardate = 0.0
        self.time_limit = 0
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the galaxy with random distribution of entities."""
        self.quadrants = [[Quadrant(row, col) for col in range(8)] for row in range(8)]
        self.total_klingons = 0
        self.total_starbases = 0

        # Distribute Klingons (original uses random distribution)
        # Approximately 15-20 Klingons total
        for row in range(8):
            for col in range(8):
                quadrant = self.quadrants[row][col]

                # Random Klingons (0-3 per quadrant, weighted toward 0-1)
                r = random.random()
                if r < 0.08:
                    quadrant.klingons = 3
                elif r < 0.20:
                    quadrant.klingons = 2
                elif r < 0.50:
                    quadrant.klingons = 1
                else:
                    quadrant.klingons = 0

                self.total_klingons += quadrant.klingons

                # Random starbases (rare, 2-4 total in galaxy)
                if random.random() < 0.04:
                    quadrant.starbases = 1
                    self.total_starbases += 1

                # Random stars (1-8 per quadrant)
                quadrant.stars = random.randint(1, 8)

        # Ensure at least one starbase
        if self.total_starbases == 0:
            row, col = random.randint(0, 7), random.randint(0, 7)
            self.quadrants[row][col].starbases = 1
            self.total_starbases = 1

        # Ensure minimum Klingons
        while self.total_klingons < 10:
            row, col = random.randint(0, 7), random.randint(0, 7)
            if self.quadrants[row][col].klingons < 3:
                self.quadrants[row][col].klingons += 1
                self.total_klingons += 1

        self.initial_klingons = self.total_klingons

        # Set game time
        self.stardate = random.randint(20, 40) * 100.0  # 2000-4000
        self.time_limit = 25 + random.randint(0, 10)  # 25-35 days

    def get_quadrant(self, row: int, col: int) -> Optional[Quadrant]:
        """Get the quadrant at the specified coordinates."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.quadrants[row][col]
        return None

    def get_lrs_data(self, center_row: int, center_col: int) -> List[List[Optional[int]]]:
        """
        Get Long Range Sensor data for the 3x3 area around the center.
        Returns a 3x3 grid of LRS values (or None if out of bounds).
        """
        result = []
        for dr in [-1, 0, 1]:
            row_data = []
            for dc in [-1, 0, 1]:
                r, c = center_row + dr, center_col + dc
                if 0 <= r < 8 and 0 <= c < 8:
                    quadrant = self.quadrants[r][c]
                    quadrant.scanned = True
                    row_data.append(quadrant.get_lrs_value())
                else:
                    row_data.append(None)
            result.append(row_data)
        return result

    def klingon_destroyed(self) -> None:
        """Called when a Klingon is destroyed."""
        self.total_klingons -= 1

    def starbase_destroyed(self, row: int, col: int) -> None:
        """Called when a starbase is destroyed."""
        if self.quadrants[row][col].starbases > 0:
            self.quadrants[row][col].starbases -= 1
            self.total_starbases -= 1

    def advance_time(self, days: float) -> None:
        """Advance the stardate."""
        self.stardate += days

    @property
    def time_remaining(self) -> float:
        """Get the remaining time in days."""
        return max(0, self.time_limit - (self.stardate % 100))

    def is_game_won(self) -> bool:
        """Check if the game is won (all Klingons destroyed)."""
        return self.total_klingons <= 0

    def is_time_up(self) -> bool:
        """Check if time has run out."""
        return self.time_remaining <= 0
