"""
input/keyboard_input.py
=======================
Pygame keyboard implementation of InputProvider.

consume_events() must be called once per frame with the pygame event list
so that is_action_just_pressed() returns accurate single-frame results.
"""

from __future__ import annotations

import pygame
from core.player_enemy import InputProvider


class KeyboardInput(InputProvider):
    """
    Maps keyboard state to the InputProvider contract used by Player.

    Axes:
        "horizontal"  — A/Left (−1) … D/Right (+1)
        "vertical"    — W/Up   (−1) … S/Down  (+1)  (unused by current move())

    Actions (just-pressed, via event queue):
        "jump"         — Space / W / Up
        "attack_light" — Z
        "attack_heavy" — X
        "use_item"     — F
    """

    # Action → pygame key(s) that trigger it
    _ACTION_KEYS: dict[str, tuple[int, ...]] = {
        "jump":   (pygame.K_k,),
        "attack": (pygame.K_j,),
    }

    def __init__(self) -> None:
        self._just_pressed: set[str] = set()

    def consume_events(self, events: list) -> None:
        """
        Call once per frame before scene.update().
        Populates the just-pressed set from KEYDOWN events.
        """
        self._just_pressed.clear()
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            for action, keys in self._ACTION_KEYS.items():
                if event.key in keys:
                    self._just_pressed.add(action)

    # ── InputProvider interface ───────────────────────────────

    def get_axis(self, axis: str) -> float:
        keys = pygame.key.get_pressed()
        if axis == "horizontal":
            return float(keys[pygame.K_d]) - float(keys[pygame.K_a])
        if axis == "vertical":
            return float(keys[pygame.K_s]) - float(keys[pygame.K_w])
        return 0.0

    def is_action_just_pressed(self, action: str) -> bool:
        return action in self._just_pressed

    def is_action_pressed(self, action: str) -> bool:
        keys = pygame.key.get_pressed()
        for k in self._ACTION_KEYS.get(action, ()):
            if keys[k]:
                return True
        return False
