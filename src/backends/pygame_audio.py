"""
backends/pygame_audio.py
========================
Pygame implementation of the two audio backend callables expected by AudioManager:
    play_sfx(sound_id: str)  — one-shot sound effect
    play_bgm(path: str)      — looping background music

Wire into AudioManager via:
    audio = PygameAudio(sfx_dir)
    manager.set_backends(audio.play_sfx, audio.play_bgm)
"""

from __future__ import annotations

from pathlib import Path

import pygame

from core.paths import SRC_DIR


class PygameAudio:

    def __init__(self, sfx_dir: str | Path | None = None) -> None:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self._sfx_dir = Path(sfx_dir) if sfx_dir else None
        self._sfx_cache: dict[str, pygame.mixer.Sound | None] = {}

    def play_sfx(self, sound_id: str) -> None:
        """Play a short sound effect by id. Silently skips missing files."""
        if sound_id not in self._sfx_cache:
            self._sfx_cache[sound_id] = self._load_sfx(sound_id)
        sound = self._sfx_cache[sound_id]
        if sound:
            sound.play()

    def play_bgm(self, path: str) -> None:
        """Start looping background music. path is relative to SRC_DIR."""
        full = SRC_DIR / path
        if not full.exists():
            return
        try:
            pygame.mixer.music.load(str(full))
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def stop_bgm(self) -> None:
        pygame.mixer.music.stop()

    def set_bgm_volume(self, volume: float) -> None:
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    def _load_sfx(self, sound_id: str) -> pygame.mixer.Sound | None:
        if self._sfx_dir is None:
            return None
        for ext in (".ogg", ".wav", ".mp3"):
            path = self._sfx_dir / (sound_id + ext)
            if path.exists():
                try:
                    return pygame.mixer.Sound(str(path))
                except pygame.error:
                    return None
        return None
