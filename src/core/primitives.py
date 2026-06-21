"""
core/primitives.py
==================
Value types, collision layers, and the event bus.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import IntFlag, auto
from typing import Any, Callable


@dataclass
class Vec2:
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalized(self) -> Vec2:
        n = self.length()
        return Vec2(self.x / n, self.y / n) if n > 0 else Vec2()

    def __repr__(self) -> str:
        return f"Vec2({self.x:.2f}, {self.y:.2f})"


@dataclass
class Rect2:
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    def overlaps(self, other: Rect2) -> bool:
        return (
            self.x < other.x + other.width
            and self.x + self.width > other.x
            and self.y < other.y + other.height
            and self.y + self.height > other.y
        )

    def contains_point(self, p: Vec2) -> bool:
        return self.x <= p.x <= self.x + self.width and self.y <= p.y <= self.y + self.height


class CollisionLayer(IntFlag):
    NONE       = 0
    PLAYER     = auto()
    ENEMY      = auto()
    PROJECTILE = auto()
    WORLD      = auto()
    PICKUP     = auto()


EventPayload = dict[str, Any]
EventHandler = Callable[[EventPayload], None]


class EventBus:
    """
    Decoupled publish-subscribe channel shared across the scene.

    Well-known events:
        damage:taken    — target, amount: int, source
        damage:dealt    — instigator, target, amount: int
        object:died     — object, killed_by
        state:changed   — object, from: str, to: str
        combo:hit       — player, combo_count: int
        pickup:collected— collector, item_id: str
        pickup:spawned  — source, position, item_id, quantity
        score:changed   — score: int, delta: int
        level:exit      — trigger
        level:complete  — level_id: str
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
