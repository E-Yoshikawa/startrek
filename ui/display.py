"""
Display module for Star Trek game.
Handles all screen output and formatting.
"""

import os
from typing import Optional

from game.galaxy import Galaxy, Quadrant, EntityType
from game.enterprise import Enterprise, Condition


class Display:
    """Handles all game display output."""

    # Symbol mappings for entities
    SYMBOLS = {
        EntityType.EMPTY: " . ",
        EntityType.ENTERPRISE: "<*>",
        EntityType.KLINGON: "+K+",
        EntityType.STARBASE: ">!<",
        EntityType.STAR: " * ",
    }

    def __init__(self, galaxy: Galaxy, enterprise: Enterprise):
        self.galaxy = galaxy
        self.enterprise = enterprise

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self) -> None:
        """Print the game header."""
        print("=" * 78)
        print("                         STAR TREK - PYTHON EDITION")
        print("=" * 78)

    def print_title_screen(self) -> None:
        """Print the title screen."""
        self.clear_screen()
        print(r"""
                                    ____
                   _______________/    \_______________
                  /    _____     /      \     _____    \
                 /    /     \___/   /\   \___/     \    \
                |    /              |  |              \    |
                |   |       ___     |  |     ___       |   |
                |   |      /   \    |  |    /   \      |   |
                 \   \    |     |   |  |   |     |    /   /
                  \   \   |     |   |  |   |     |   /   /
                   \   \  |_____|   \__/   |_____|  /   /
                    \   \_______________________   /   /
                     \          ENTERPRISE      \_/   /
                      \_____________________________/

        """)
        print("=" * 78)
        print("                         STAR TREK - PYTHON EDITION")
        print("                      Based on the 1978 BASIC version")
        print("=" * 78)
        print()

    def print_mission_briefing(self) -> None:
        """Print the mission briefing."""
        print("\n" + "=" * 78)
        print("                            MISSION BRIEFING")
        print("=" * 78)
        print()
        print("  Captain, your mission is to destroy the Klingon invasion force.")
        print()
        print(f"  Klingon ships to destroy: {self.galaxy.total_klingons}")
        print(f"  Starbases available:      {self.galaxy.total_starbases}")
        print(f"  Starting stardate:        {self.galaxy.stardate:.1f}")
        print(f"  Time limit:               {self.galaxy.time_limit} days")
        print()
        print("  Available commands:")
        print("    NAV - Navigate      SRS - Short Range Scan   LRS - Long Range Scan")
        print("    PHA - Phasers       TOR - Torpedoes          SHE - Shields")
        print("    DAM - Damage Report COM - Computer           XXX - Resign")
        print()
        print("=" * 78)

    def print_status_bar(self) -> None:
        """Print the status bar at the top of the screen."""
        quadrant = self.galaxy.get_quadrant(
            self.enterprise.quadrant_row,
            self.enterprise.quadrant_col
        )
        condition = self.enterprise.get_condition(quadrant.klingons)

        print(f"STARDATE: {self.galaxy.stardate:.1f}    "
              f"TIME LEFT: {self.galaxy.time_remaining:.0f} DAYS    "
              f"KLINGONS: {self.galaxy.total_klingons}    "
              f"STARBASES: {self.galaxy.total_starbases}")
        print()
        print(f"QUADRANT: {quadrant.name}  [{self.enterprise.quadrant_row+1},"
              f"{self.enterprise.quadrant_col+1}]"
              f"              CONDITION: {condition.value}")
        print("-" * 78)

    def print_short_range_scan(self) -> None:
        """Print the short range sensor display."""
        quadrant = self.galaxy.get_quadrant(
            self.enterprise.quadrant_row,
            self.enterprise.quadrant_col
        )

        if not quadrant.sector_map:
            quadrant.initialize_sector_map()
            quadrant.place_enterprise(
                self.enterprise.sector_row,
                self.enterprise.sector_col
            )

        print("SHORT RANGE SENSORS:")
        print("    1   2   3   4   5   6   7   8")
        print("  +" + "---+" * 8)

        for row in range(8):
            row_str = f"{row+1} |"
            for col in range(8):
                entity = quadrant.sector_map[row][col]
                row_str += self.SYMBOLS.get(entity, " ? ") + "|"
            print(row_str)
            print("  +" + "---+" * 8)

    def print_combined_display(self) -> None:
        """Print combined SRS and LRS with status."""
        quadrant = self.galaxy.get_quadrant(
            self.enterprise.quadrant_row,
            self.enterprise.quadrant_col
        )

        if not quadrant.sector_map:
            quadrant.initialize_sector_map()
            quadrant.place_enterprise(
                self.enterprise.sector_row,
                self.enterprise.sector_col
            )

        # Get LRS data
        lrs_data = self.galaxy.get_lrs_data(
            self.enterprise.quadrant_row,
            self.enterprise.quadrant_col
        )

        # Build SRS display
        srs_lines = ["SHORT RANGE SENSORS:"]
        srs_lines.append("    1   2   3   4   5   6   7   8")
        srs_lines.append("  +" + "---+" * 8)

        for row in range(8):
            row_str = f"{row+1} |"
            for col in range(8):
                entity = quadrant.sector_map[row][col]
                row_str += self.SYMBOLS.get(entity, " ? ") + "|"
            srs_lines.append(row_str)
            srs_lines.append("  +" + "---+" * 8)

        # Build LRS and status display
        lrs_lines = ["LONG RANGE SENSORS:"]
        lrs_lines.append("+-----+-----+-----+")
        for row in lrs_data:
            cells = []
            for val in row:
                if val is None:
                    cells.append(" *** ")
                else:
                    cells.append(f" {val:03d} ")
            lrs_lines.append("|" + "|".join(cells) + "|")
            lrs_lines.append("+-----+-----+-----+")

        # Status lines
        status_lines = ["", "STATUS:"]
        status_lines.append(f"  ENERGY:    {self.enterprise.energy:5d}")
        status_lines.append(f"  SHIELDS:   {self.enterprise.shields:5d}")
        status_lines.append(f"  TORPEDOES: {self.enterprise.torpedoes:5d}")

        # Check for damage
        has_damage = any(v < 0 for v in self.enterprise.damage.values())
        status_lines.append(f"  DAMAGE:    {'YES' if has_damage else 'NONE'}")

        # Print combined display
        print()
        max_srs = len(srs_lines)
        max_side = max(len(lrs_lines), len(status_lines))

        for i in range(max(max_srs, max_side + 1)):
            # SRS column (left)
            if i < len(srs_lines):
                srs_part = f"{srs_lines[i]:<45}"
            else:
                srs_part = " " * 45

            # LRS/Status column (right)
            if i == 0:
                side_part = lrs_lines[0] if lrs_lines else ""
            elif i <= len(lrs_lines) - 1:
                side_part = lrs_lines[i]
            elif i - len(lrs_lines) < len(status_lines):
                side_part = status_lines[i - len(lrs_lines)]
            else:
                side_part = ""

            print(srs_part + side_part)

    def print_command_prompt(self) -> None:
        """Print the command prompt."""
        print("-" * 78)
        print("COMMANDS: NAV  SRS  LRS  PHA  TOR  SHE  DAM  COM  XXX")

    def print_game_over(self, victory: bool) -> None:
        """Print game over screen."""
        print()
        print("=" * 78)
        if victory:
            print("                         *** CONGRATULATIONS ***")
            print()
            print("        You have successfully destroyed the Klingon invasion force!")
            print()
            # Calculate rating
            days_used = self.galaxy.time_limit - self.galaxy.time_remaining
            if days_used < 1:
                days_used = 1
            rating = (self.galaxy.initial_klingons / days_used) * 1000
            print(f"        Klingons destroyed: {self.galaxy.initial_klingons}")
            print(f"        Days used:          {days_used:.1f}")
            print(f"        Rating:             {rating:.0f}")
            print()
            if rating > 1000:
                print("        You have been promoted to ADMIRAL!")
            elif rating > 500:
                print("        You have been promoted to COMMODORE!")
            elif rating > 200:
                print("        You have been commended for your service.")
            else:
                print("        Your performance was... adequate.")
        else:
            print("                           *** GAME OVER ***")
            print()
            if self.enterprise.destroyed:
                print("        The Enterprise has been destroyed.")
                print("        You have failed in your mission.")
            elif self.galaxy.time_remaining <= 0:
                print("        You have run out of time!")
                print("        The Federation has fallen to the Klingon Empire.")
            elif self.galaxy.total_starbases <= 0 and self.enterprise.energy < 100:
                print("        With no starbases and low energy,")
                print("        the Enterprise is stranded in space.")
            print()
            print(f"        Klingons remaining: {self.galaxy.total_klingons}")

        print("=" * 78)

    def print_entering_quadrant(self) -> None:
        """Print message when entering a new quadrant."""
        quadrant = self.galaxy.get_quadrant(
            self.enterprise.quadrant_row,
            self.enterprise.quadrant_col
        )

        print()
        print(f"Now entering quadrant {quadrant.name}")
        print()

        if quadrant.klingons > 0:
            print(f"*** RED ALERT! {quadrant.klingons} Klingon(s) detected! ***")
            print()

        if quadrant.starbases > 0:
            print("A Federation starbase is in this quadrant.")
            print()

    def print_message(self, message: str) -> None:
        """Print a game message."""
        if message:
            print()
            print(message)
            print()

    def wait_for_key(self, prompt: str = "Press Enter to continue...") -> None:
        """Wait for user to press Enter."""
        input(prompt)
