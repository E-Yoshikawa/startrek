"""
Enterprise class for Star Trek game.
Handles ship resources, damage, and systems.
"""

import random
from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum


class ShipSystem(Enum):
    """Ship systems that can be damaged."""
    WARP_ENGINES = "Warp Engines"
    SHORT_RANGE_SENSORS = "Short Range Sensors"
    LONG_RANGE_SENSORS = "Long Range Sensors"
    PHASER_CONTROL = "Phaser Control"
    PHOTON_TUBES = "Photon Tubes"
    DAMAGE_CONTROL = "Damage Control"
    SHIELD_CONTROL = "Shield Control"
    LIBRARY_COMPUTER = "Library Computer"


class Condition(Enum):
    """Ship condition status."""
    GREEN = "GREEN"    # No enemies in quadrant
    YELLOW = "YELLOW"  # Low energy
    RED = "RED"        # Enemies in quadrant
    DOCKED = "DOCKED"  # Docked at starbase


@dataclass
class Enterprise:
    """
    Represents the USS Enterprise.
    Manages resources, position, and damage state.
    """

    # Position
    quadrant_row: int = 0
    quadrant_col: int = 0
    sector_row: int = 0
    sector_col: int = 0

    # Resources
    energy: int = 3000
    max_energy: int = 3000
    torpedoes: int = 10
    max_torpedoes: int = 10
    shields: int = 0

    # State
    docked: bool = False
    destroyed: bool = False

    # Damage state for each system (negative = damaged, 0 = operational)
    # Value represents repair time remaining
    damage: Dict[ShipSystem, float] = field(default_factory=dict)

    def __post_init__(self):
        # Initialize all systems as operational
        if not self.damage:
            self.damage = {system: 0.0 for system in ShipSystem}

    def reset(self) -> None:
        """Reset ship to initial state."""
        self.energy = self.max_energy
        self.torpedoes = self.max_torpedoes
        self.shields = 0
        self.docked = False
        self.destroyed = False
        self.damage = {system: 0.0 for system in ShipSystem}

    def dock(self) -> None:
        """Dock at starbase - restore all resources."""
        self.docked = True
        self.energy = self.max_energy
        self.torpedoes = self.max_torpedoes
        self.shields = 0  # Shields lowered when docked

    def undock(self) -> None:
        """Undock from starbase."""
        self.docked = False

    def repair_all(self) -> None:
        """Repair all systems (when docked)."""
        for system in ShipSystem:
            self.damage[system] = 0.0

    def get_condition(self, klingons_in_quadrant: int) -> Condition:
        """Get the current ship condition."""
        if self.docked:
            return Condition.DOCKED
        elif klingons_in_quadrant > 0:
            return Condition.RED
        elif self.energy < self.max_energy * 0.1:
            return Condition.YELLOW
        else:
            return Condition.GREEN

    def is_system_damaged(self, system: ShipSystem) -> bool:
        """Check if a system is damaged."""
        return self.damage.get(system, 0) < 0

    def get_damage_report(self) -> Dict[ShipSystem, float]:
        """Get damage report for all systems."""
        return self.damage.copy()

    def apply_damage(self, amount: int) -> str:
        """
        Apply damage to the ship.
        Returns a message describing what happened.
        """
        messages = []

        # Shields absorb damage first
        if self.shields > 0:
            if self.shields >= amount:
                self.shields -= amount
                messages.append(f"Shields absorb hit. Shields now at {self.shields}.")
                amount = 0
            else:
                amount -= self.shields
                messages.append(f"Shields depleted!")
                self.shields = 0

        # Remaining damage hits energy and possibly damages systems
        if amount > 0:
            self.energy -= amount
            messages.append(f"Hit! {amount} units damage. Energy now {self.energy}.")

            # Chance to damage a random system
            if random.random() < 0.6:  # 60% chance
                system = random.choice(list(ShipSystem))
                damage_amount = random.uniform(-0.5, -3.0)
                self.damage[system] += damage_amount
                messages.append(f"*** {system.value} damaged! ***")

        # Check for destruction
        if self.energy <= 0:
            self.destroyed = True
            messages.append("*** ENTERPRISE DESTROYED ***")

        return "\n".join(messages)

    def repair_systems(self, time_elapsed: float) -> list:
        """
        Repair systems over time.
        Returns list of systems that were repaired.
        """
        repaired = []
        repair_rate = 1.0 if self.docked else 0.1

        for system in ShipSystem:
            if self.damage[system] < 0:
                self.damage[system] += repair_rate * time_elapsed
                if self.damage[system] >= 0:
                    self.damage[system] = 0
                    repaired.append(system)

        return repaired

    def use_energy(self, amount: int) -> bool:
        """
        Use energy for an action.
        Returns True if there was enough energy.
        """
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def transfer_to_shields(self, amount: int) -> bool:
        """
        Transfer energy to shields.
        Returns True if successful.
        """
        if amount < 0:
            # Transfer from shields to energy
            transfer = min(-amount, self.shields)
            self.shields -= transfer
            self.energy += transfer
            return True
        elif amount <= self.energy:
            self.energy -= amount
            self.shields += amount
            return True
        return False

    def fire_torpedo(self) -> bool:
        """
        Fire a torpedo.
        Returns True if a torpedo was available.
        """
        if self.torpedoes > 0:
            self.torpedoes -= 1
            return True
        return False

    def set_position(self, quad_row: int, quad_col: int,
                     sect_row: int, sect_col: int) -> None:
        """Set the ship's position."""
        self.quadrant_row = quad_row
        self.quadrant_col = quad_col
        self.sector_row = sect_row
        self.sector_col = sect_col

    @property
    def total_energy(self) -> int:
        """Get total energy (energy + shields)."""
        return self.energy + self.shields

    def can_warp(self) -> bool:
        """Check if warp engines are operational."""
        return not self.is_system_damaged(ShipSystem.WARP_ENGINES)

    def can_use_srs(self) -> bool:
        """Check if short range sensors are operational."""
        return not self.is_system_damaged(ShipSystem.SHORT_RANGE_SENSORS)

    def can_use_lrs(self) -> bool:
        """Check if long range sensors are operational."""
        return not self.is_system_damaged(ShipSystem.LONG_RANGE_SENSORS)

    def can_fire_phasers(self) -> bool:
        """Check if phasers are operational."""
        return not self.is_system_damaged(ShipSystem.PHASER_CONTROL)

    def can_fire_torpedoes(self) -> bool:
        """Check if torpedo tubes are operational."""
        return not self.is_system_damaged(ShipSystem.PHOTON_TUBES)

    def can_use_shields(self) -> bool:
        """Check if shield control is operational."""
        return not self.is_system_damaged(ShipSystem.SHIELD_CONTROL)

    def can_use_computer(self) -> bool:
        """Check if library computer is operational."""
        return not self.is_system_damaged(ShipSystem.LIBRARY_COMPUTER)
