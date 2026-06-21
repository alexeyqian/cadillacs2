"""
managers/audio_manager.py
==========================
Pooled SFX and BGM crossfading.
Subscribes to game events — gameplay code never calls audio directly.
"""

from __future__ import annotations

from typing import Callable


class AudioManager:
    """
    All sound triggering happens through event subscriptions,
    never via direct calls from gameplay code.

    BGM states:
        'calm'   — ambient level music
        'combat' — battle music (crossfade when enemies are nearby)
        'boss'   — boss battle music
    """

    def __init__(self) -> None:
        self._sfx_pool: dict[str, list] = {}
        self._bgm_track: str = ""
        self._play_sfx_fn: Callable[[str], None] | None = None
        self._play_bgm_fn: Callable[[str], None] | None = None

    def set_backends(
        self,
        play_sfx: Callable[[str], None],
        play_bgm: Callable[[str], None],
    ) -> None:
        """Inject audio backend functions (e.g. pygame.mixer calls)."""
        self._play_sfx_fn = play_sfx
        self._play_bgm_fn = play_bgm

    def on_attach(self, bus) -> None:
        bus.on("damage:taken",     self._on_hit)
        bus.on("object:died",      self._on_death)
        bus.on("pickup:collected", self._on_pickup)
        bus.on("combo:hit",        self._on_combo)
        bus.on("state:changed",    self._on_state_changed)

    def _on_hit(self, payload) -> None:
        self._sfx("hit_sound")

    def _on_death(self, payload) -> None:
        obj = payload.get("object")
        if obj and obj.has_tag("player"):
            self._sfx("player_death")
        else:
            self._sfx("enemy_death")

    def _on_pickup(self, payload) -> None:
        self._sfx("pickup_chime")

    def _on_combo(self, payload) -> None:
        count = payload.get("combo_count", 1)
        # Escalating pitch — clamp to available variants
        variant = min(count, 5)
        self._sfx(f"combo_hit_{variant}")

    def _on_state_changed(self, payload) -> None:
        to = payload.get("to", "")
        if to == "dead" and payload.get("object", None) and \
           payload["object"].has_tag("boss"):
            self._bgm("victory_fanfare")

    def play_bgm(self, track: str) -> None:
        if track != self._bgm_track:
            self._bgm_track = track
            self._bgm(track)

    def _sfx(self, sound_id: str) -> None:
        if self._play_sfx_fn:
            self._play_sfx_fn(sound_id)

    def _bgm(self, track_id: str) -> None:
        if self._play_bgm_fn:
            self._play_bgm_fn(track_id)
