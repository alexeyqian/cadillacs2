"""
primitives.py
=============
Value types, collision layers, and the event bus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntFlag, auto
from typing import Any, Callable


# ─────────────────────────────────────────────
# Value types
# ─────────────────────────────────────────────

@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    def __repr__(self) -> str:
        return f"Vec2({self.x:.2f}, {self.y:.2f})"


@dataclass
class Rect2:
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0


# ─────────────────────────────────────────────
# Collision layers  (bit-flags)
# ─────────────────────────────────────────────

class CollisionLayer(IntFlag):
    NONE       = 0
    PLAYER     = auto()
    ENEMY      = auto()
    PROJECTILE = auto()
    WORLD      = auto()
    PICKUP     = auto()


# ─────────────────────────────────────────────
# Event bus
# Simple publish-subscribe; shared across the scene.
# Mirrors Godot signals / Unity UnityEvent.
# ─────────────────────────────────────────────

EventPayload = dict[str, Any]
EventHandler = Callable[[EventPayload], None]


class EventBus:
    """
    Decoupled publish-subscribe channel.
    Objects emit named events; listeners subscribe without holding
    direct references to the emitter.

    Well-known event names:
        "damage:taken"   — payload: target, amount, source
        "object:died"    — payload: object, killed_by
        "state:changed"  — payload: object, from, to
        "combo:hit"      — payload: player, combo_count
        "pickup:spawned" — payload: source, position, item_id, quantity
    """

    def __init__(self) -> None:
        self._listeners: dict[str, list[EventHandler]] = {}

    def on(self, event: str, handler: EventHandler) -> None:
        self._listeners.setdefault(event, []).append(handler)

    def off(self, event: str, handler: EventHandler) -> None:
        listeners = self._listeners.get(event, [])
        if handler in listeners:
            listeners.remove(handler)

    def emit(self, event: str, payload: EventPayload) -> None:
        for handler in list(self._listeners.get(event, [])):
            handler(payload)