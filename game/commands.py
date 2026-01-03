"""
Command handlers for Star Trek game.
Implements NAV, SRS, LRS, PHA, TOR, SHE, DAM, COM commands.
"""

import math
import random
from typing import Tuple, Optional, Callable
from dataclasses import dataclass

from game.galaxy import Galaxy, Quadrant, EntityType
from game.enterprise import Enterprise, ShipSystem
from game.combat import (
    fire_phasers, fire_torpedo, klingon_attack,
    calculate_distance, calculate_torpedo_direction
)
from ui.sound import SoundSystem


@dataclass
class CommandResult:
    """Result of a command execution."""
    success: bool
    message: str
    time_used: float = 0.0
    trigger_klingon_attack: bool = False
    quit_game: bool = False


class CommandHandler:
    """Handles all game commands."""

    def __init__(self, galaxy: Galaxy, enterprise: Enterprise, sound: SoundSystem):
        self.galaxy = galaxy
        self.enterprise = enterprise
        self.sound = sound
        self._input_func: Callable[[str], str] = input

    def set_input_function(self, func: Callable[[str], str]) -> None:
        """Set custom input function (for testing)."""
        self._input_func = func

    def get_input(self, prompt: str) -> str:
        """Get input from user."""
        return self._input_func(prompt)

    def get_current_quadrant(self) -> Quadrant:
        """Get the current quadrant."""
        return self.galaxy.get_quadrant(
            self.enterprise.quadrant_row,
            self.enterprise.quadrant_col
        )

    def execute_nav(self) -> CommandResult:
        """
        NAV - Navigate the Enterprise.
        Prompts for course (1-9) and warp factor (0-8).
        """
        if not self.enterprise.can_warp():
            return CommandResult(False, "Warp engines are damaged!")

        try:
            course_str = self.get_input("Course (1-9): ")
            course = float(course_str)
            if course < 1 or course > 9:
                return CommandResult(False, "Invalid course. Use 1-9.")
        except ValueError:
            return CommandResult(False, "Invalid course input.")

        try:
            warp_str = self.get_input("Warp factor (0-8): ")
            warp = float(warp_str)
            if warp < 0 or warp > 8:
                return CommandResult(False, "Invalid warp factor. Use 0-8.")
        except ValueError:
            return CommandResult(False, "Invalid warp factor input.")

        if warp == 0:
            return CommandResult(True, "Navigation cancelled.")

        # Calculate energy required
        # Original: energy = warp_factor * 8 (per sector moved)
        sectors_to_move = int(warp * 8)
        energy_required = sectors_to_move + 10  # Base cost + movement

        if energy_required > self.enterprise.energy:
            return CommandResult(
                False,
                f"Insufficient energy. Required: {energy_required}, "
                f"Available: {self.enterprise.energy}"
            )

        # Undock if docked
        if self.enterprise.docked:
            self.enterprise.undock()

        # Calculate direction deltas
        direction_deltas = {
            1: (0, 1),    # East
            2: (-1, 1),   # Northeast
            3: (-1, 0),   # North
            4: (-1, -1),  # Northwest
            5: (0, -1),   # West
            6: (1, -1),   # Southwest
            7: (1, 0),    # South
            8: (1, 1),    # Southeast
        }

        base_dir = int(course) if course < 9 else 1
        fraction = course - int(course)
        next_dir = base_dir + 1 if base_dir < 8 else 1

        dr1, dc1 = direction_deltas[base_dir]
        dr2, dc2 = direction_deltas[next_dir]

        dr = dr1 * (1 - fraction) + dr2 * fraction
        dc = dc1 * (1 - fraction) + dc2 * fraction

        # Normalize
        magnitude = math.sqrt(dr ** 2 + dc ** 2)
        if magnitude > 0:
            dr /= magnitude
            dc /= magnitude

        # Remove Enterprise from current position
        current_quadrant = self.get_current_quadrant()
        current_quadrant.remove_enterprise(
            self.enterprise.sector_row,
            self.enterprise.sector_col
        )

        # Move the Enterprise
        new_sect_row = float(self.enterprise.sector_row)
        new_sect_col = float(self.enterprise.sector_col)
        new_quad_row = self.enterprise.quadrant_row
        new_quad_col = self.enterprise.quadrant_col
        crossed_quadrant = False

        for _ in range(sectors_to_move):
            new_sect_row += dr
            new_sect_col += dc

            # Check for quadrant boundary crossing
            if new_sect_row < 0:
                new_quad_row -= 1
                new_sect_row += 8
                crossed_quadrant = True
            elif new_sect_row >= 8:
                new_quad_row += 1
                new_sect_row -= 8
                crossed_quadrant = True

            if new_sect_col < 0:
                new_quad_col -= 1
                new_sect_col += 8
                crossed_quadrant = True
            elif new_sect_col >= 8:
                new_quad_col += 1
                new_sect_col -= 8
                crossed_quadrant = True

            # Check galaxy boundaries
            if new_quad_row < 0 or new_quad_row >= 8 or \
               new_quad_col < 0 or new_quad_col >= 8:
                self.sound.play_hit()
                # Restore Enterprise to original position
                current_quadrant.sector_map[self.enterprise.sector_row][self.enterprise.sector_col] = EntityType.ENTERPRISE
                return CommandResult(
                    False,
                    "You have attempted to cross the galactic barrier.\n"
                    "Navigation aborted - returning to previous position."
                )

        # Use energy
        self.enterprise.use_energy(energy_required)

        # Update position
        final_sect_row = int(round(new_sect_row)) % 8
        final_sect_col = int(round(new_sect_col)) % 8

        # Get new quadrant and place Enterprise
        if crossed_quadrant:
            self.sound.play_warp()
            new_quadrant = self.galaxy.get_quadrant(new_quad_row, new_quad_col)
            new_quadrant.initialize_sector_map()
            actual_row, actual_col = new_quadrant.place_enterprise(
                final_sect_row, final_sect_col
            )
        else:
            new_quadrant = current_quadrant
            # Check for collision with objects
            entity = new_quadrant.get_entity_at(final_sect_row, final_sect_col)
            if entity != EntityType.EMPTY:
                # Find nearest empty sector
                actual_row, actual_col = new_quadrant._find_empty_sector()
            else:
                actual_row, actual_col = final_sect_row, final_sect_col
            # Place Enterprise at new position
            new_quadrant.sector_map[actual_row][actual_col] = EntityType.ENTERPRISE

        self.enterprise.set_position(
            new_quad_row, new_quad_col,
            actual_row, actual_col
        )

        # Check for docking
        if new_quadrant.is_adjacent_to_starbase(actual_row, actual_col):
            self.enterprise.dock()
            self.sound.play_dock()
            dock_msg = "\n*** DOCKED AT STARBASE ***\nShields lowered. Repairs and resupply available."
        else:
            dock_msg = ""

        # Calculate time used (warp 1 = 1 day, warp 8 = 0.125 days)
        time_used = 1.0 / warp if warp > 0 else 0

        # Build message
        messages = [f"Warp {warp:.1f} engaged."]
        if crossed_quadrant:
            messages.append(f"Entering quadrant {new_quadrant.name}")
        messages.append(f"Position: Sector [{actual_row+1},{actual_col+1}]")
        messages.append(f"Energy used: {energy_required}")
        if dock_msg:
            messages.append(dock_msg)

        return CommandResult(
            success=True,
            message="\n".join(messages),
            time_used=time_used,
            trigger_klingon_attack=new_quadrant.klingons > 0 and not self.enterprise.docked
        )

    def execute_srs(self) -> CommandResult:
        """SRS - Short Range Sensor Scan."""
        if not self.enterprise.can_use_srs():
            return CommandResult(False, "Short range sensors are damaged!")

        # SRS is always displayed on screen, so just refresh (no message needed)
        return CommandResult(True, "")

    def execute_lrs(self) -> CommandResult:
        """LRS - Long Range Sensor Scan."""
        if not self.enterprise.can_use_lrs():
            return CommandResult(False, "Long range sensors are damaged!")

        # Mark surrounding quadrants as scanned
        lrs_data = self.galaxy.get_lrs_data(
            self.enterprise.quadrant_row,
            self.enterprise.quadrant_col
        )

        # Build display
        lines = ["LONG RANGE SENSOR SCAN", ""]
        lines.append("+-----+-----+-----+")
        for row in lrs_data:
            cells = []
            for val in row:
                if val is None:
                    cells.append(" *** ")
                else:
                    cells.append(f" {val:03d} ")
            lines.append("|" + "|".join(cells) + "|")
            lines.append("+-----+-----+-----+")

        return CommandResult(True, "\n".join(lines))

    def execute_pha(self) -> CommandResult:
        """PHA - Fire Phasers."""
        if not self.enterprise.can_fire_phasers():
            return CommandResult(False, "Phaser control is damaged!")

        quadrant = self.get_current_quadrant()
        if not quadrant.klingon_ships:
            return CommandResult(False, "No Klingons in this quadrant!")

        try:
            energy_str = self.get_input(
                f"Phaser energy to fire (available: {self.enterprise.energy}): "
            )
            energy = int(energy_str)
        except ValueError:
            return CommandResult(False, "Invalid energy amount.")

        if energy <= 0:
            return CommandResult(True, "Phasers not fired.")

        self.sound.play_phaser()
        result = fire_phasers(self.enterprise, quadrant, energy)

        if result.klingons_destroyed > 0:
            self.sound.play_explosion()
            for _ in range(result.klingons_destroyed):
                self.galaxy.klingon_destroyed()

        return CommandResult(
            success=result.success,
            message=result.message,
            trigger_klingon_attack=quadrant.klingons > 0 and result.success
        )

    def execute_tor(self) -> CommandResult:
        """TOR - Fire Photon Torpedoes."""
        if not self.enterprise.can_fire_torpedoes():
            return CommandResult(False, "Photon tubes are damaged!")

        if self.enterprise.torpedoes <= 0:
            return CommandResult(False, "No torpedoes remaining!")

        try:
            dir_str = self.get_input(
                f"Torpedo course (1-9), torpedoes remaining: {self.enterprise.torpedoes}: "
            )
            direction = float(dir_str)
        except ValueError:
            return CommandResult(False, "Invalid direction.")

        if direction < 1 or direction > 9:
            return CommandResult(False, "Invalid direction. Use 1-9.")

        self.sound.play_torpedo()
        quadrant = self.get_current_quadrant()
        result = fire_torpedo(self.enterprise, quadrant, direction)

        if result.klingons_destroyed > 0:
            self.sound.play_explosion()
            for _ in range(result.klingons_destroyed):
                self.galaxy.klingon_destroyed()

        return CommandResult(
            success=result.success,
            message=result.message,
            trigger_klingon_attack=quadrant.klingons > 0
        )

    def execute_she(self) -> CommandResult:
        """SHE - Shield Control."""
        if not self.enterprise.can_use_shields():
            return CommandResult(False, "Shield control is damaged!")

        print(f"Current shield energy: {self.enterprise.shields}")
        print(f"Current energy: {self.enterprise.energy}")
        print(f"Total: {self.enterprise.total_energy}")

        try:
            energy_str = self.get_input("Energy to transfer to shields: ")
            energy = int(energy_str)
        except ValueError:
            return CommandResult(False, "Invalid energy amount.")

        if energy == 0:
            return CommandResult(True, "No change to shields.")

        if energy > 0 and energy > self.enterprise.energy:
            return CommandResult(
                False,
                f"Insufficient energy. Available: {self.enterprise.energy}"
            )

        if energy < 0 and -energy > self.enterprise.shields:
            return CommandResult(
                False,
                f"Cannot transfer more than current shields: {self.enterprise.shields}"
            )

        self.enterprise.transfer_to_shields(energy)

        return CommandResult(
            True,
            f"Shield energy now: {self.enterprise.shields}\n"
            f"Available energy: {self.enterprise.energy}"
        )

    def execute_dam(self) -> CommandResult:
        """DAM - Damage Control Report."""
        damage_report = self.enterprise.get_damage_report()

        lines = ["DAMAGE CONTROL REPORT", ""]
        lines.append(f"{'System':<25} {'Status':<15}")
        lines.append("-" * 40)

        any_damage = False
        for system, value in damage_report.items():
            if value < 0:
                status = f"DAMAGED ({-value:.1f} repairs needed)"
                any_damage = True
            else:
                status = "Operational"
            lines.append(f"{system.value:<25} {status:<15}")

        if self.enterprise.docked and any_damage:
            lines.append("")
            repair_prompt = self.get_input("Repair all systems? (Y/N): ")
            if repair_prompt.upper().startswith('Y'):
                self.enterprise.repair_all()
                lines.append("All systems repaired.")

        return CommandResult(True, "\n".join(lines))

    def execute_com(self) -> CommandResult:
        """COM - Library Computer."""
        if not self.enterprise.can_use_computer():
            return CommandResult(False, "Library computer is damaged!")

        print("\nCOMPUTER FUNCTIONS:")
        print("0 = Cumulative Galactic Record")
        print("1 = Status Report")
        print("2 = Photon Torpedo Data")
        print("3 = Starbase Navigation Data")
        print("4 = Direction/Distance Calculator")
        print("5 = Galactic Region Map")

        try:
            func_str = self.get_input("Computer function (0-5): ")
            func = int(func_str)
        except ValueError:
            return CommandResult(False, "Invalid function.")

        if func == 0:
            return self._com_galactic_record()
        elif func == 1:
            return self._com_status_report()
        elif func == 2:
            return self._com_torpedo_data()
        elif func == 3:
            return self._com_starbase_nav()
        elif func == 4:
            return self._com_direction_calculator()
        elif func == 5:
            return self._com_region_map()
        else:
            return CommandResult(False, "Invalid function.")

    def _com_galactic_record(self) -> CommandResult:
        """Display cumulative galactic record."""
        lines = ["CUMULATIVE GALACTIC RECORD", ""]
        lines.append("    " + "   ".join([str(i+1) for i in range(8)]))
        lines.append("  +" + "----+" * 8)

        for row in range(8):
            row_data = []
            for col in range(8):
                q = self.galaxy.get_quadrant(row, col)
                if q.scanned:
                    row_data.append(f"{q.get_lrs_value():03d}")
                else:
                    row_data.append("***")
            lines.append(f"{row+1} | " + " | ".join(row_data) + " |")
            lines.append("  +" + "----+" * 8)

        return CommandResult(True, "\n".join(lines))

    def _com_status_report(self) -> CommandResult:
        """Display status report."""
        lines = ["STATUS REPORT", ""]
        lines.append(f"Stardate:           {self.galaxy.stardate:.1f}")
        lines.append(f"Time Remaining:     {self.galaxy.time_remaining:.1f} days")
        lines.append(f"Klingons Remaining: {self.galaxy.total_klingons}")
        lines.append(f"Starbases:          {self.galaxy.total_starbases}")
        lines.append(f"Energy:             {self.enterprise.energy}")
        lines.append(f"Shields:            {self.enterprise.shields}")
        lines.append(f"Torpedoes:          {self.enterprise.torpedoes}")

        return CommandResult(True, "\n".join(lines))

    def _com_torpedo_data(self) -> CommandResult:
        """Calculate torpedo firing direction to each Klingon."""
        quadrant = self.get_current_quadrant()
        if not quadrant.klingon_ships:
            return CommandResult(True, "No Klingons in this quadrant.")

        lines = ["PHOTON TORPEDO DATA", ""]
        lines.append(f"{'Klingon Position':<20} {'Direction':<12} {'Distance':<10}")
        lines.append("-" * 42)

        for klingon in quadrant.klingon_ships:
            direction = calculate_torpedo_direction(
                self.enterprise,
                klingon.sector_row,
                klingon.sector_col
            )
            distance = calculate_distance(
                self.enterprise.sector_row, self.enterprise.sector_col,
                klingon.sector_row, klingon.sector_col
            )
            lines.append(
                f"[{klingon.sector_row+1},{klingon.sector_col+1}]"
                f"{'':<14} {direction:<12.2f} {distance:<10.2f}"
            )

        return CommandResult(True, "\n".join(lines))

    def _com_starbase_nav(self) -> CommandResult:
        """Calculate navigation to nearest starbase."""
        quadrant = self.get_current_quadrant()
        if quadrant.starbase_pos:
            sb_row, sb_col = quadrant.starbase_pos
            direction = calculate_torpedo_direction(
                self.enterprise, sb_row, sb_col
            )
            distance = calculate_distance(
                self.enterprise.sector_row, self.enterprise.sector_col,
                sb_row, sb_col
            )
            return CommandResult(
                True,
                f"STARBASE NAVIGATION DATA\n\n"
                f"Starbase in this quadrant at [{sb_row+1},{sb_col+1}]\n"
                f"Direction: {direction:.2f}\n"
                f"Distance: {distance:.2f} sectors"
            )

        # Find nearest starbase in galaxy
        min_dist = float('inf')
        nearest = None
        for row in range(8):
            for col in range(8):
                q = self.galaxy.get_quadrant(row, col)
                if q.starbases > 0:
                    dist = calculate_distance(
                        self.enterprise.quadrant_row,
                        self.enterprise.quadrant_col,
                        row, col
                    )
                    if dist < min_dist:
                        min_dist = dist
                        nearest = (row, col, q.name)

        if nearest:
            return CommandResult(
                True,
                f"STARBASE NAVIGATION DATA\n\n"
                f"No starbase in current quadrant.\n"
                f"Nearest starbase: {nearest[2]} [{nearest[0]+1},{nearest[1]+1}]\n"
                f"Quadrant distance: {min_dist:.2f}"
            )

        return CommandResult(True, "No starbases remaining!")

    def _com_direction_calculator(self) -> CommandResult:
        """Calculate direction between two points."""
        try:
            print("Enter starting coordinates:")
            r1 = int(self.get_input("  Row (1-8): ")) - 1
            c1 = int(self.get_input("  Column (1-8): ")) - 1
            print("Enter destination coordinates:")
            r2 = int(self.get_input("  Row (1-8): ")) - 1
            c2 = int(self.get_input("  Column (1-8): ")) - 1
        except ValueError:
            return CommandResult(False, "Invalid coordinates.")

        if not (0 <= r1 < 8 and 0 <= c1 < 8 and 0 <= r2 < 8 and 0 <= c2 < 8):
            return CommandResult(False, "Coordinates out of range.")

        # Create temporary object to calculate direction
        class TempPos:
            sector_row = r1
            sector_col = c1

        direction = calculate_torpedo_direction(TempPos(), r2, c2)
        distance = calculate_distance(r1, c1, r2, c2)

        return CommandResult(
            True,
            f"DIRECTION/DISTANCE\n\n"
            f"From [{r1+1},{c1+1}] to [{r2+1},{c2+1}]\n"
            f"Direction: {direction:.2f}\n"
            f"Distance: {distance:.2f}"
        )

    def _com_region_map(self) -> CommandResult:
        """Display galactic region names."""
        from data.quadrant_names import get_quadrant_name

        lines = ["GALACTIC REGION MAP", ""]
        for row in range(8):
            row_names = []
            for col in range(8):
                name = get_quadrant_name(row, col)
                # Truncate to 12 chars
                row_names.append(f"{name[:12]:<12}")
            lines.append(" ".join(row_names))

        return CommandResult(True, "\n".join(lines))

    def execute_xxx(self) -> CommandResult:
        """XXX - Exit game."""
        confirm = self.get_input("Are you sure you want to quit? (Y/N): ")
        if confirm.upper().startswith('Y'):
            return CommandResult(True, "Game terminated.", quit_game=True)
        return CommandResult(True, "Returning to game.")

    def process_klingon_attack(self) -> str:
        """Process Klingon counter-attack."""
        quadrant = self.get_current_quadrant()
        if quadrant.klingons > 0 and not self.enterprise.docked:
            self.sound.play_hit()
            return klingon_attack(self.enterprise, quadrant)
        return ""
