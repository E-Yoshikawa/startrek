"""
Sound system for Star Trek game.
Supports three modes: OFF, BEEP, and EFFECTS.
"""

import sys
import time
from enum import Enum
from typing import Optional

# Try to import pygame and numpy for EFFECTS mode
try:
    import pygame
    import numpy as np
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class SoundMode(Enum):
    """Sound mode enumeration."""
    OFF = 0      # No sound
    BEEP = 1     # Simple terminal beep
    EFFECTS = 2  # Rich sound effects (requires pygame)


class SoundSystem:
    """
    Sound system with three modes:
    - OFF: No sound output
    - BEEP: Simple terminal beep sounds
    - EFFECTS: Rich synthesized sound effects
    """

    SAMPLE_RATE = 44100

    def __init__(self, mode: SoundMode = SoundMode.BEEP):
        self._mode = SoundMode.OFF
        self._initialized = False
        self._sounds: dict = {}
        self.set_mode(mode)

    def set_mode(self, mode: SoundMode) -> bool:
        """
        Set the sound mode.
        Returns True if mode was set successfully.
        """
        if mode == SoundMode.EFFECTS:
            if not PYGAME_AVAILABLE:
                print("Warning: pygame/numpy not available. Falling back to BEEP mode.")
                self._mode = SoundMode.BEEP
                return False

            if not self._initialized:
                try:
                    pygame.mixer.init(frequency=self.SAMPLE_RATE, size=-16, channels=1)
                    self._initialized = True
                    self._generate_sounds()
                except Exception as e:
                    print(f"Warning: Could not initialize sound. Falling back to BEEP mode. ({e})")
                    self._mode = SoundMode.BEEP
                    return False

        self._mode = mode
        return True

    def get_mode(self) -> SoundMode:
        """Get the current sound mode."""
        return self._mode

    def _generate_sounds(self) -> None:
        """Generate all sound effects."""
        if not PYGAME_AVAILABLE or not self._initialized:
            return

        self._sounds = {
            'phaser': self._generate_phaser_sound(),
            'torpedo': self._generate_torpedo_sound(),
            'explosion': self._generate_explosion_sound(),
            'warp': self._generate_warp_sound(),
            'hit': self._generate_hit_sound(),
            'dock': self._generate_dock_sound(),
            'gameover': self._generate_gameover_sound(),
            'victory': self._generate_victory_sound(),
            'alert': self._generate_alert_sound(),
        }

    def _make_sound(self, wave: 'np.ndarray') -> Optional['pygame.mixer.Sound']:
        """Create a pygame Sound object from wave data."""
        if not PYGAME_AVAILABLE:
            return None
        try:
            return pygame.sndarray.make_sound(wave.astype(np.int16))
        except Exception:
            return None

    def _generate_phaser_sound(self) -> Optional['pygame.mixer.Sound']:
        """Generate phaser beam sound - high to low frequency sweep."""
        duration = 0.3
        samples = int(self.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)

        # Frequency sweep from 2000Hz to 500Hz
        freq = np.linspace(2000, 500, samples)
        phase = np.cumsum(2 * np.pi * freq / self.SAMPLE_RATE)
        wave = np.sin(phase) * 32767

        # Fade out
        fade = np.linspace(1, 0, samples)
        wave = wave * fade

        return self._make_sound(wave)

    def _generate_torpedo_sound(self) -> Optional['pygame.mixer.Sound']:
        """Generate torpedo launch sound - short burst."""
        duration = 0.15
        samples = int(self.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)

        # Low frequency pulse
        freq = 150
        wave = np.sign(np.sin(2 * np.pi * freq * t)) * 32767

        # Quick fade
        fade = np.exp(-t * 15)
        wave = wave * fade

        return self._make_sound(wave)

    def _generate_explosion_sound(self) -> Optional['pygame.mixer.Sound']:
        """Generate explosion sound - noise with decay."""
        duration = 0.4
        samples = int(self.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)

        # White noise
        noise = np.random.uniform(-1, 1, samples)

        # Low-pass filter effect (simple moving average)
        window = 50
        noise = np.convolve(noise, np.ones(window)/window, mode='same')

        # Exponential decay
        decay = np.exp(-t * 8)
        wave = noise * decay * 32767

        return self._make_sound(wave)

    def _generate_warp_sound(self) -> Optional['pygame.mixer.Sound']:
        """Generate warp sound - rising pitch."""
        duration = 0.5
        samples = int(self.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)

        # Frequency sweep from 100Hz to 1000Hz
        freq = np.linspace(100, 1000, samples)
        phase = np.cumsum(2 * np.pi * freq / self.SAMPLE_RATE)
        wave = np.sin(phase) * 32767

        # Fade in and out
        fade_in = np.minimum(t * 10, 1)
        fade_out = np.maximum(1 - (t - 0.4) * 10, 0)
        fade = fade_in * fade_out
        wave = wave * fade

        return self._make_sound(wave)

    def _generate_hit_sound(self) -> Optional['pygame.mixer.Sound']:
        """Generate hit/damage sound - low rumble."""
        duration = 0.3
        samples = int(self.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)

        # Low frequency with noise
        freq = 80
        wave = np.sin(2 * np.pi * freq * t)
        noise = np.random.uniform(-0.3, 0.3, samples)
        wave = (wave + noise) * 32767

        # Decay
        decay = np.exp(-t * 6)
        wave = wave * decay

        return self._make_sound(wave)

    def _generate_dock_sound(self) -> Optional['pygame.mixer.Sound']:
        """Generate docking sound - pleasant chime."""
        duration = 0.3
        samples = int(self.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)

        # Two-tone chime
        wave = np.sin(2 * np.pi * 880 * t) + np.sin(2 * np.pi * 1320 * t)
        wave = wave / 2 * 32767

        # Fade out
        fade = np.exp(-t * 5)
        wave = wave * fade

        return self._make_sound(wave)

    def _generate_gameover_sound(self) -> Optional['pygame.mixer.Sound']:
        """Generate game over sound - descending tones."""
        duration = 1.0
        samples = int(self.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)

        # Descending frequency
        freq = np.linspace(400, 100, samples)
        phase = np.cumsum(2 * np.pi * freq / self.SAMPLE_RATE)
        wave = np.sin(phase) * 32767

        # Slow fade
        fade = np.exp(-t * 2)
        wave = wave * fade

        return self._make_sound(wave)

    def _generate_victory_sound(self) -> Optional['pygame.mixer.Sound']:
        """Generate victory fanfare - ascending tones."""
        duration = 1.0
        samples = int(self.SAMPLE_RATE * duration)

        # Create melody: C-E-G-C (major chord arpeggio)
        notes = [262, 330, 392, 523]  # C4, E4, G4, C5
        note_samples = samples // 4

        wave = np.array([])
        for freq in notes:
            t = np.linspace(0, 0.25, note_samples, False)
            note = np.sin(2 * np.pi * freq * t)
            fade = np.exp(-t * 3)
            wave = np.concatenate([wave, note * fade])

        wave = wave * 32767
        return self._make_sound(wave)

    def _generate_alert_sound(self) -> Optional['pygame.mixer.Sound']:
        """Generate alert/red alert sound."""
        duration = 0.5
        samples = int(self.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, samples, False)

        # Alternating two tones
        freq1 = 600
        freq2 = 800
        switch = (t * 8).astype(int) % 2
        wave = np.where(switch, np.sin(2 * np.pi * freq1 * t), np.sin(2 * np.pi * freq2 * t))
        wave = wave * 32767

        return self._make_sound(wave)

    def _beep(self, count: int = 1, delay: float = 0.1) -> None:
        """Emit terminal beep sound."""
        for i in range(count):
            sys.stdout.write('\a')
            sys.stdout.flush()
            if i < count - 1:
                time.sleep(delay)

    def play_phaser(self) -> None:
        """Play phaser firing sound."""
        if self._mode == SoundMode.OFF:
            return
        elif self._mode == SoundMode.BEEP:
            self._beep(2, 0.05)
        elif self._mode == SoundMode.EFFECTS and 'phaser' in self._sounds:
            self._sounds['phaser'].play()

    def play_torpedo(self) -> None:
        """Play torpedo launch sound."""
        if self._mode == SoundMode.OFF:
            return
        elif self._mode == SoundMode.BEEP:
            self._beep(1)
        elif self._mode == SoundMode.EFFECTS and 'torpedo' in self._sounds:
            self._sounds['torpedo'].play()

    def play_explosion(self) -> None:
        """Play explosion sound."""
        if self._mode == SoundMode.OFF:
            return
        elif self._mode == SoundMode.BEEP:
            self._beep(3, 0.08)
        elif self._mode == SoundMode.EFFECTS and 'explosion' in self._sounds:
            self._sounds['explosion'].play()

    def play_warp(self) -> None:
        """Play warp drive sound."""
        if self._mode == SoundMode.OFF:
            return
        elif self._mode == SoundMode.BEEP:
            self._beep(2, 0.15)
        elif self._mode == SoundMode.EFFECTS and 'warp' in self._sounds:
            self._sounds['warp'].play()

    def play_hit(self) -> None:
        """Play hit/damage sound."""
        if self._mode == SoundMode.OFF:
            return
        elif self._mode == SoundMode.BEEP:
            self._beep(1)
        elif self._mode == SoundMode.EFFECTS and 'hit' in self._sounds:
            self._sounds['hit'].play()

    def play_dock(self) -> None:
        """Play docking sound."""
        if self._mode == SoundMode.OFF:
            return
        elif self._mode == SoundMode.BEEP:
            self._beep(2, 0.2)
        elif self._mode == SoundMode.EFFECTS and 'dock' in self._sounds:
            self._sounds['dock'].play()

    def play_gameover(self) -> None:
        """Play game over sound."""
        if self._mode == SoundMode.OFF:
            return
        elif self._mode == SoundMode.BEEP:
            self._beep(5, 0.15)
        elif self._mode == SoundMode.EFFECTS and 'gameover' in self._sounds:
            self._sounds['gameover'].play()

    def play_victory(self) -> None:
        """Play victory sound."""
        if self._mode == SoundMode.OFF:
            return
        elif self._mode == SoundMode.BEEP:
            self._beep(4, 0.1)
        elif self._mode == SoundMode.EFFECTS and 'victory' in self._sounds:
            self._sounds['victory'].play()

    def play_alert(self) -> None:
        """Play alert sound."""
        if self._mode == SoundMode.OFF:
            return
        elif self._mode == SoundMode.BEEP:
            self._beep(3, 0.1)
        elif self._mode == SoundMode.EFFECTS and 'alert' in self._sounds:
            self._sounds['alert'].play()

    def cleanup(self) -> None:
        """Clean up sound resources."""
        if self._initialized and PYGAME_AVAILABLE:
            try:
                pygame.mixer.quit()
            except Exception:
                pass
            self._initialized = False
            self._sounds.clear()
