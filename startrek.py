#!/usr/bin/env python3
"""
Star Trek - Python Edition

A faithful recreation of the classic 1978 BASIC Star Trek game.
Originally by Mike Mayfield (1971), enhanced by Bob Leedom (1974).

Based on the PC-8801 version.

Usage:
    python startrek.py [--sound off|beep|effects]

Sound modes:
    off     - No sound
    beep    - Simple terminal beep sounds
    effects - Rich synthesized effects (requires pygame)
"""

import sys
import random
import argparse

# Add the current directory to path for imports
sys.path.insert(0, '.')

from game.galaxy import Galaxy
from game.enterprise import Enterprise
from game.commands import CommandHandler
from ui.display import Display
from ui.sound import SoundSystem, SoundMode


class StarTrekGame:
    """Main game class."""

    def __init__(self, sound_mode: SoundMode = SoundMode.BEEP):
        self.galaxy = Galaxy()
        self.enterprise = Enterprise()
        self.sound = SoundSystem(sound_mode)
        self.display = Display(self.galaxy, self.enterprise)
        self.commands = CommandHandler(self.galaxy, self.enterprise, self.sound)
        self.running = False

    def initialize_game(self) -> None:
        """Initialize a new game."""
        # Reset galaxy and enterprise
        self.galaxy = Galaxy()
        self.enterprise = Enterprise()
        self.display = Display(self.galaxy, self.enterprise)
        self.commands = CommandHandler(self.galaxy, self.enterprise, self.sound)

        # Place Enterprise in random starting position
        start_quad_row = random.randint(0, 7)
        start_quad_col = random.randint(0, 7)
        start_sect_row = random.randint(0, 7)
        start_sect_col = random.randint(0, 7)

        # Initialize starting quadrant
        start_quadrant = self.galaxy.get_quadrant(start_quad_row, start_quad_col)
        start_quadrant.initialize_sector_map()

        # Place Enterprise
        actual_row, actual_col = start_quadrant.place_enterprise(
            start_sect_row, start_sect_col
        )
        self.enterprise.set_position(
            start_quad_row, start_quad_col,
            actual_row, actual_col
        )

        # Mark starting quadrant as scanned
        start_quadrant.scanned = True

    def show_title_and_briefing(self) -> None:
        """Show title screen and mission briefing."""
        self.display.print_title_screen()
        self.display.wait_for_key()
        self.display.clear_screen()
        self.display.print_mission_briefing()
        self.display.wait_for_key()

    def game_loop(self) -> None:
        """Main game loop."""
        self.running = True

        # Initial display
        self.display.clear_screen()
        self.display.print_header()
        self.display.print_status_bar()
        self.display.print_entering_quadrant()
        self.display.print_combined_display()

        while self.running:
            # Check for game over conditions
            if self.galaxy.is_game_won():
                self.sound.play_victory()
                self.display.print_game_over(victory=True)
                break

            if self.enterprise.destroyed:
                self.sound.play_gameover()
                self.display.print_game_over(victory=False)
                break

            if self.galaxy.is_time_up():
                self.sound.play_gameover()
                self.display.print_game_over(victory=False)
                break

            # Get command
            self.display.print_command_prompt()
            try:
                command = input("COMMAND? ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print("\nGame interrupted.")
                break

            if not command:
                continue

            # Execute command
            result = self.execute_command(command)

            if result:
                # Display result
                self.display.print_message(result.message)

                # Update time if command used time
                if result.time_used > 0:
                    self.galaxy.advance_time(result.time_used)

                    # Repair systems over time
                    repaired = self.enterprise.repair_systems(result.time_used)
                    for system in repaired:
                        print(f"*** {system.value} has been repaired ***")

                # Process Klingon counter-attack
                if result.trigger_klingon_attack:
                    attack_msg = self.commands.process_klingon_attack()
                    if attack_msg:
                        self.display.print_message(attack_msg)

                # Check for quit
                if result.quit_game:
                    self.running = False
                    break

            # For commands that display important info, wait for user before clearing
            wait_commands = ['LRS', 'COM', 'DAM', 'TOR', 'PHA']
            if command in wait_commands and result:
                self.display.wait_for_key()

            # Refresh display
            self.display.clear_screen()
            self.display.print_header()
            self.display.print_status_bar()
            self.display.print_combined_display()

    def execute_command(self, command: str):
        """Execute a game command."""
        command = command[:3].upper()  # Only first 3 chars matter

        command_map = {
            'NAV': self.commands.execute_nav,
            'SRS': self.commands.execute_srs,
            'LRS': self.commands.execute_lrs,
            'PHA': self.commands.execute_pha,
            'TOR': self.commands.execute_tor,
            'SHE': self.commands.execute_she,
            'DAM': self.commands.execute_dam,
            'COM': self.commands.execute_com,
            'XXX': self.commands.execute_xxx,
        }

        if command in command_map:
            return command_map[command]()
        else:
            print(f"Unknown command: {command}")
            print("Valid commands: NAV SRS LRS PHA TOR SHE DAM COM XXX")
            return None

    def run(self) -> None:
        """Run the game."""
        try:
            self.show_title_and_briefing()
            self.initialize_game()
            self.game_loop()
        except KeyboardInterrupt:
            print("\n\nGame interrupted by user.")
        finally:
            self.sound.cleanup()

        # Ask to play again
        print()
        try:
            again = input("Play again? (Y/N): ").strip().upper()
            if again.startswith('Y'):
                self.run()
        except (EOFError, KeyboardInterrupt):
            pass

        print("\nThank you for playing Star Trek!")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Star Trek - Python Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Sound Modes:
  off     - No sound output
  beep    - Simple terminal beep sounds (default)
  effects - Rich synthesized effects (requires pygame and numpy)

Examples:
  python startrek.py                    # Play with beep sounds
  python startrek.py --sound off        # Play silently
  python startrek.py --sound effects    # Play with rich sound effects
        """
    )

    parser.add_argument(
        '--sound', '-s',
        choices=['off', 'beep', 'effects'],
        default='beep',
        help='Sound mode (default: beep)'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Map sound argument to SoundMode
    sound_modes = {
        'off': SoundMode.OFF,
        'beep': SoundMode.BEEP,
        'effects': SoundMode.EFFECTS,
    }
    sound_mode = sound_modes[args.sound]

    # Create and run game
    game = StarTrekGame(sound_mode)
    game.run()


if __name__ == '__main__':
    main()
