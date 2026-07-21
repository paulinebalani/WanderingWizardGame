"""
sound_manager.py  –  Centralised audio controller for Wandering Wizard
=======================================================================

Usage
-----
    from sound_manager import SoundManager
    sounds = SoundManager()          # call once in WanderingWizard.__init__
    sounds.play_music()              # start BGM loop
    sounds.play_sfx('wizard_death')  # one-shot SFX
    sounds.play_sfx('game_over')     # triggered on 3rd death / game-over screen

Settings panel integration
--------------------------
    sounds.music_on     – bool, toggled by Settings panel
    sounds.sfx_on       – bool, toggled by Settings panel
    sounds.toggle_music()
    sounds.toggle_sfx()

Sound catalogue
---------------
  BGM  (loops whole game):
      425470__sieuamthanh__thu-nghiem-ien-am-1.wav

  SFX  (one-shots):
      'wizard_death'   → 369005__flying_deer_fx__death-01-mouth-fx-man-voice.wav
      'dome_kill'      → 364929__jofae__game-die.mp3
      'lightning_kill' → 350506__spennnyyy__extremely-close-thunder-no-rain.wav
      'game_over'      → 524741__lilmati__game-over-08.wav
"""

import os
import pygame


# ── File paths (relative to this file) ────────────────────────────────────────
_BASE       = os.path.dirname(__file__)
_SFX_DIR    = os.path.join(_BASE, 'sounds')   # put .wav/.mp3 files here

_MUSIC_FILE = os.path.join(_SFX_DIR, 'bgm.wav')

_SFX_FILES  = {
    'wizard_death'   : os.path.join(_SFX_DIR, 'ouch.wav'),
    'dome_kill'      : os.path.join(_SFX_DIR, 'burst.mp3'),
    'lightning_kill' : os.path.join(_SFX_DIR, 'lightning.wav'),
    'game_over'      : os.path.join(_SFX_DIR, 'game_over.wav'),
}

_MUSIC_VOLUME = 0.60   # 0.0 – 1.0  (BGM is deliberately softer)
_SFX_VOLUME   = 1.0


class SoundManager:
    """
    Manages background music and all one-shot sound effects.

    Attributes
    ----------
    music_on : bool   – whether BGM is currently enabled
    sfx_on   : bool   – whether SFX are currently enabled
    """

    def __init__(self):
        # pygame.mixer is already initialised by pygame.init() in WanderingWizard,
        # but calling init() again is safe (it's a no-op if already done).
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.music_on : bool = True
        self.sfx_on   : bool = True

        self._sfx : dict = {}
        self._load_assets()

        # Track whether the game-over sound has already fired this round
        # so it plays exactly once per game-over event.
        self._game_over_played : bool = False

    # ── Asset loading ──────────────────────────────────────────────────────────
    def _load_assets(self):
        """Load all SFX into memory; silently skip missing files."""
        for key, path in _SFX_FILES.items():
            if os.path.isfile(path):
                try:
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(_SFX_VOLUME)
                    self._sfx[key] = sound
                except pygame.error as exc:
                    print(f"[SoundManager] Could not load '{path}': {exc}")
            else:
                print(f"[SoundManager] File not found: '{path}'")

    # ── Music ──────────────────────────────────────────────────────────────────
    def play_music(self):
        """Start the BGM loop (call once when the game window opens)."""
        if not os.path.isfile(_MUSIC_FILE):
            print(f"[SoundManager] Music file not found: '{_MUSIC_FILE}'")
            return
        try:
            pygame.mixer.music.load(_MUSIC_FILE)
            pygame.mixer.music.set_volume(_MUSIC_VOLUME if self.music_on else 0.0)
            pygame.mixer.music.play(-1)   # -1 = infinite loop
        except pygame.error as exc:
            print(f"[SoundManager] Could not start music: {exc}")

    def stop_music(self):
        pygame.mixer.music.stop()

    def toggle_music(self):
        """Flip music_on and immediately mute/unmute the BGM stream."""
        self.music_on = not self.music_on
        if self.music_on:
            pygame.mixer.music.set_volume(_MUSIC_VOLUME)
            if not pygame.mixer.music.get_busy():
                self.play_music()   # restart if it was stopped
        else:
            pygame.mixer.music.set_volume(0.0)

    # ── SFX ───────────────────────────────────────────────────────────────────
    def play_sfx(self, key: str):
        """
        Play a one-shot sound effect.

        Parameters
        ----------
        key : str
            One of: 'wizard_death', 'dome_kill', 'lightning_kill', 'game_over'
        """
        if not self.sfx_on:
            return
        sound = self._sfx.get(key)
        if sound:
            sound.play()
        else:
            print(f"[SoundManager] Unknown or unloaded SFX key: '{key}'")

    def toggle_sfx(self):
        """Flip sfx_on (already-playing sounds are unaffected)."""
        self.sfx_on = not self.sfx_on

    # ── Game-over helper ──────────────────────────────────────────────────────
    def trigger_game_over_sound(self):
        """
        Play the game-over jingle exactly once per game-over event.
        Call from WanderingWizard whenever game_over_active first becomes True,
        or when the quit/restart buttons appear.
        Reset by calling reset_game_over_flag() on _restart_game().
        """
        if not self._game_over_played:
            self._game_over_played = True
            self.play_sfx('game_over')

    def reset_game_over_flag(self):
        """Reset so the game-over sound can fire again next round."""
        self._game_over_played = False