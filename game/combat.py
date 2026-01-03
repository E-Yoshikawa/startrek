"""
Combat system for Star Trek game.
Implements original BASIC damage formulas.

Original BASIC formulas:
- Distance: FND(D) = SQR((K(I,1)-S1)^2 + (K(I,2)-S2)^2)
- Phaser damage: H = INT((H1/FND(0)) * (RND(1)+2))
  where H1 = INT(X/K3) (energy divided by number of Klingons)
- Random multiplier: 2.0 to 3.0
"""

import math
import random
from typing import List, Tuple, Optional
from dataclasses import dataclass

from game.galaxy import Quadrant, Klingon, EntityType
from game.enterprise import Enterprise


@dataclass
class CombatResult:
    """Result of a combat action."""
    success: bool
    message: str
    klingons_destroyed: int = 0
    damage_dealt: List[Tuple[int, int, int]] = None  # [(row, col, damage), ...]

    def __post_init__(self):
        if self.damage_dealt is None:
            self.damage_dealt = []


def calculate_distance(row1: int, col1: int, row2: int, col2: int) -> float:
    """
    Calculate Euclidean distance between two positions.
    Original BASIC: FND(D) = SQR((K(I,1)-S1)^2 + (K(I,2)-S2)^2)
    """
    return math.sqrt((row1 - row2) ** 2 + (col1 - col2) ** 2)


def fire_phasers(enterprise: Enterprise, quadrant: Quadrant,
                 energy_amount: int) -> CombatResult:
    """
    Fire phasers at all Klingons in the quadrant.

    Original BASIC damage formula:
    - Energy is divided equally among all Klingons
    - Damage = (energy_per_target / distance) * random(2.0 to 3.0)
    - If damage > Klingon energy, Klingon is destroyed

    Args:
        enterprise: The Enterprise ship
        quadrant: Current quadrant
        energy_amount: Amount of energy to use for phasers

    Returns:
        CombatResult with details of the attack
    """
    if not enterprise.can_fire_phasers():
        return CombatResult(False, "Phaser control is damaged!")

    if energy_amount <= 0:
        return CombatResult(False, "Invalid phaser energy amount.")

    if energy_amount > enterprise.energy:
        return CombatResult(False, f"Insufficient energy. Available: {enterprise.energy}")

    klingons = quadrant.klingon_ships
    if not klingons:
        return CombatResult(False, "No Klingons in this quadrant!")

    # Use energy
    enterprise.use_energy(energy_amount)

    # Check for phaser overheating (original: >1500 units risks damage)
    if energy_amount > 1500:
        overheat_chance = (energy_amount - 1500) / 1500
        if random.random() < overheat_chance:
            enterprise.damage[enterprise.damage.__class__.PHASER_CONTROL] = -random.uniform(1.0, 3.0)
            return CombatResult(False,
                f"Phasers overheated and damaged! {energy_amount} units wasted.")

    # Divide energy among Klingons
    energy_per_target = energy_amount / len(klingons)

    messages = [f"Phasers fired with {energy_amount} units of energy."]
    destroyed_count = 0
    damage_dealt = []
    klingons_to_remove = []

    for klingon in klingons:
        distance = calculate_distance(
            enterprise.sector_row, enterprise.sector_col,
            klingon.sector_row, klingon.sector_col
        )

        # Avoid division by zero
        if distance < 0.1:
            distance = 0.1

        # Original formula: damage = (energy/distance) * random(2.0-3.0)
        random_multiplier = random.uniform(2.0, 3.0)
        damage = int((energy_per_target / distance) * random_multiplier)

        damage_dealt.append((klingon.sector_row, klingon.sector_col, damage))

        if damage >= klingon.energy:
            # Klingon destroyed
            messages.append(
                f"*** Klingon at [{klingon.sector_row+1},{klingon.sector_col+1}] destroyed! ***"
            )
            klingons_to_remove.append(klingon)
            destroyed_count += 1
        else:
            # Klingon damaged
            klingon.energy -= damage
            messages.append(
                f"Hit Klingon at [{klingon.sector_row+1},{klingon.sector_col+1}] "
                f"for {damage} damage. Energy remaining: {klingon.energy}"
            )

    # Remove destroyed Klingons
    for klingon in klingons_to_remove:
        quadrant.remove_klingon(klingon.sector_row, klingon.sector_col)

    return CombatResult(
        success=True,
        message="\n".join(messages),
        klingons_destroyed=destroyed_count,
        damage_dealt=damage_dealt
    )


def fire_torpedo(enterprise: Enterprise, quadrant: Quadrant,
                 direction: float) -> CombatResult:
    """
    Fire a photon torpedo in the specified direction.

    Direction is 1-9 (like a compass):
        4  3  2
         \\ | /
      5 -- E -- 1
         / | \\
        6  7  8

    Args:
        enterprise: The Enterprise ship
        quadrant: Current quadrant
        direction: Direction to fire (1-9)

    Returns:
        CombatResult with details of the attack
    """
    if not enterprise.can_fire_torpedoes():
        return CombatResult(False, "Photon tubes are damaged!")

    if enterprise.torpedoes <= 0:
        return CombatResult(False, "No torpedoes remaining!")

    if direction < 1 or direction > 9:
        return CombatResult(False, "Invalid direction. Use 1-9.")

    # Use torpedo
    if not enterprise.fire_torpedo():
        return CombatResult(False, "Failed to fire torpedo!")

    # Convert direction to delta coordinates
    # Direction mapping (1-9):
    # 4=NW, 3=N, 2=NE
    # 5=W,  E,   1=E
    # 6=SW, 7=S, 8=SE
    direction_deltas = {
        1: (0, 1),    # East
        2: (-1, 1),   # Northeast
        3: (-1, 0),   # North
        4: (-1, -1),  # Northwest
        5: (0, -1),   # West
        6: (1, -1),   # Southwest
        7: (1, 0),    # South
        8: (1, 1),    # Southeast
        9: (0, 1),    # East (same as 1)
    }

    # Handle fractional directions
    base_dir = int(direction)
    if base_dir == 9:
        base_dir = 1

    fraction = direction - int(direction)
    next_dir = base_dir + 1 if base_dir < 8 else 1

    dr1, dc1 = direction_deltas[base_dir]
    dr2, dc2 = direction_deltas[next_dir]

    # Interpolate between directions
    dr = dr1 * (1 - fraction) + dr2 * fraction
    dc = dc1 * (1 - fraction) + dc2 * fraction

    # Normalize to step size
    step_size = 1.0
    if dr != 0 or dc != 0:
        magnitude = math.sqrt(dr ** 2 + dc ** 2)
        dr = dr / magnitude * step_size
        dc = dc / magnitude * step_size

    # Track torpedo path
    messages = [f"Torpedo fired in direction {direction:.1f}!"]
    current_row = float(enterprise.sector_row)
    current_col = float(enterprise.sector_col)

    # Simulate torpedo travel
    for step in range(15):  # Max 15 steps across quadrant
        current_row += dr
        current_col += dc

        row = int(round(current_row))
        col = int(round(current_col))

        # Check if torpedo left the quadrant
        if row < 0 or row >= 8 or col < 0 or col >= 8:
            messages.append("Torpedo missed - left quadrant.")
            return CombatResult(True, "\n".join(messages), 0)

        # Check what's at this position
        entity = quadrant.get_entity_at(row, col)

        if entity == EntityType.KLINGON:
            # Hit a Klingon!
            messages.append(f"*** Torpedo hit Klingon at [{row+1},{col+1}]! ***")
            quadrant.remove_klingon(row, col)
            messages.append("*** KLINGON DESTROYED! ***")
            return CombatResult(True, "\n".join(messages), 1)

        elif entity == EntityType.STAR:
            # Hit a star - torpedo absorbed
            messages.append(f"Torpedo impacted star at [{row+1},{col+1}] - absorbed.")
            return CombatResult(True, "\n".join(messages), 0)

        elif entity == EntityType.STARBASE:
            # Hit starbase - destroyed!
            messages.append(f"*** Torpedo hit STARBASE at [{row+1},{col+1}]! ***")
            messages.append("*** STARBASE DESTROYED! ***")
            messages.append("You will be court-martialed for this!")
            quadrant.starbases = 0
            quadrant.starbase_pos = None
            quadrant.sector_map[row][col] = EntityType.EMPTY
            return CombatResult(True, "\n".join(messages), 0)

    messages.append("Torpedo missed - no target hit.")
    return CombatResult(True, "\n".join(messages), 0)


def klingon_attack(enterprise: Enterprise, quadrant: Quadrant) -> str:
    """
    All Klingons in the quadrant attack the Enterprise.

    Original BASIC formula:
    - Each Klingon fires with damage = (klingon_energy / distance) * random(0 to 1)

    Args:
        enterprise: The Enterprise ship
        quadrant: Current quadrant

    Returns:
        Message describing the attack
    """
    if enterprise.docked:
        return "Starbase shields protect the Enterprise."

    klingons = quadrant.klingon_ships
    if not klingons:
        return ""

    messages = []

    for klingon in klingons:
        distance = calculate_distance(
            enterprise.sector_row, enterprise.sector_col,
            klingon.sector_row, klingon.sector_col
        )

        if distance < 0.1:
            distance = 0.1

        # Original formula: damage = (klingon_energy / distance) * random
        # Random factor gives some variance to attacks
        random_factor = random.uniform(0.5, 1.0)
        damage = int((klingon.energy / distance) * random_factor)

        messages.append(f"Klingon at [{klingon.sector_row+1},{klingon.sector_col+1}] fires!")

        # Apply damage to Enterprise
        damage_msg = enterprise.apply_damage(damage)
        messages.append(damage_msg)

        if enterprise.destroyed:
            break

    return "\n".join(messages)


def calculate_torpedo_direction(enterprise: Enterprise,
                                 target_row: int, target_col: int) -> float:
    """
    Calculate the direction to fire a torpedo to hit a target.

    Direction system (1-9):
        4  3  2
         \\ | /
      5 -- E -- 1
         / | \\
        6  7  8

    Returns direction value 1-9.
    """
    dr = target_row - enterprise.sector_row
    dc = target_col - enterprise.sector_col

    if dr == 0 and dc == 0:
        return 1.0  # Same position, default to East

    # Convert to angle (radians)
    # atan2(-dr, dc) because:
    # - row increases downward, so negative dr = upward = north
    # - col increases rightward = east
    angle = math.atan2(-dr, dc)

    # Convert angle to direction (1-9 system)
    # angle 0 = East = direction 1
    # angle π/2 = North = direction 3
    # angle π = West = direction 5
    # angle -π/2 = South = direction 7

    # Map angle (-π to π) to direction (1 to 9)
    direction = 1.0 + (angle * 4.0 / math.pi)

    # Normalize to 1-9 range
    if direction < 1:
        direction += 8
    if direction > 9:
        direction -= 8

    return direction


def get_direction_to_starbase(enterprise: Enterprise,
                               quadrant: Quadrant) -> Optional[Tuple[float, float]]:
    """
    Get the direction and distance to the nearest starbase in the quadrant.

    Returns (direction, distance) or None if no starbase.
    """
    if quadrant.starbase_pos is None:
        return None

    sb_row, sb_col = quadrant.starbase_pos
    distance = calculate_distance(
        enterprise.sector_row, enterprise.sector_col,
        sb_row, sb_col
    )

    direction = calculate_torpedo_direction(enterprise, sb_row, sb_col)

    return (direction, distance)
