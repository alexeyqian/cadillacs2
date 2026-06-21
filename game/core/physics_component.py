from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .component_base import ComponentBase
from .primitives import Rect2, Vec2

if TYPE_CHECKING:
    from .game_object import GameObject

# ─────────────────────────────────────────────
# PhysicsComponent
# ─────────────────────────────────────────────

class PhysicsComponent(ComponentBase):
    """
    Per-entity 2-D physics state: velocity, gravity, friction, knockback.
    Actual collision resolution lives in the PhysicsSystem — this component
    only owns the per-object state and integrates each frame.
    """

    def __init__(self) -> None:
        self.velocity: Vec2 = Vec2()
        self.gravity: float = 980.0         # px/s²
        self.max_fall_speed: float = 1200.0
        self.is_grounded: bool = False
        self.friction: float = 0.18         # velocity.x *= (1 - friction) per frame
        self.immovable: bool = False        # set during hit-stun

        self.on_landed: Callable[[], None] | None = None
        self.on_fell: Callable[[], None] | None = None

    def update(self, dt: float) -> None:
        if self.immovable:
            return

        if not self.is_grounded:
            self.velocity.y = min(
                self.velocity.y + self.gravity * dt,
                self.max_fall_speed,
            )

        if self.is_grounded:
            self.velocity.x *= (1.0 - self.friction)
            if abs(self.velocity.x) < 0.5:
                self.velocity.x = 0.0

        pos = self.owner.position
        pos.x += self.velocity.x * dt
        pos.y += self.velocity.y * dt

    def apply_impulse(self, impulse: Vec2) -> None:
        self.velocity.x += impulse.x
        self.velocity.y += impulse.y

    def apply_knockback(self, knockback: Vec2) -> None:
        self.velocity.x = knockback.x
        self.velocity.y = knockback.y
        self.is_grounded = False

