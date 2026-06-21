from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .component_base import ComponentBase
from .primitives import Rect2, Vec2

if TYPE_CHECKING:
    from .game_object import GameObject

# ─────────────────────────────────────────────
# CollisionComponent
# ─────────────────────────────────────────────

@dataclass
class HitboxDef:
    id: str
    rect: Rect2             # offset from owner position
    damage: float
    knockback: Vec2
    active: bool = False


class CollisionComponent(ComponentBase):
    """
    Stores the hurtbox (receives damage) and named attack hitboxes (deal damage).
    The PhysicsSystem queries active hitboxes each frame.
    """

    def __init__(self) -> None:
        self.hurtbox: Rect2 = Rect2(0, 0, 32, 64)
        self.hitboxes: dict[str, HitboxDef] = {}
        self.layer: int = 0
        self.mask: int = 0

        self.on_hit: Callable[[HitboxDef, "GameObject"], None] | None = None
        self.on_hurtbox_hit: Callable[[DamageInfo], None] | None = None

    def update(self, dt: float) -> None:
        pass   # resolution handled by PhysicsSystem

    def activate_hitbox(self, hitbox_id: str) -> None:
        if hitbox_id in self.hitboxes:
            self.hitboxes[hitbox_id].active = True

    def deactivate_hitbox(self, hitbox_id: str) -> None:
        if hitbox_id in self.hitboxes:
            self.hitboxes[hitbox_id].active = False

    def deactivate_all_hitboxes(self) -> None:
        for h in self.hitboxes.values():
            h.active = False

    def get_active_hitboxes(self) -> list[HitboxDef]:
        return [h for h in self.hitboxes.values() if h.active]

