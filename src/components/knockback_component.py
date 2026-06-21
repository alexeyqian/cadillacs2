"""
components/knockback_component.py
==================================
Manages hit-stun freeze frames and knockback separately from PhysicsComponent.

Sequence on hit:
  1. freeze_frames set → zero velocity, pause animation.
  2. After freeze: apply knockback_velocity to PhysicsComponent.
  3. hit_stun_frames counts down; physics.immovable = True during stun.
"""

from __future__ import annotations

from core.component_base import ComponentBase
from core.primitives import Vec2


class KnockbackComponent(ComponentBase):

    def __init__(self) -> None:
        self.freeze_frames: int = 0
        self.hit_stun_frames: int = 0
        self.knockback_velocity: Vec2 = Vec2()
        self._freeze_timer: float = 0.0
        self._stun_timer: float = 0.0

    _FPS: float = 60.0

    def apply(self, knockback: Vec2, freeze_frames: int = 3, stun_frames: int = 12) -> None:
        """Called by CollisionSystem when a hit lands."""
        self.knockback_velocity = Vec2(knockback.x, knockback.y)
        self.freeze_frames = freeze_frames
        self.hit_stun_frames = stun_frames
        self._freeze_timer = freeze_frames / self._FPS
        self._stun_timer = (freeze_frames + stun_frames) / self._FPS

        from core.components import PhysicsComponent
        phys = self.owner.get_component(PhysicsComponent)
        if phys:
            phys.velocity = Vec2()
            phys.immovable = True

    def update(self, dt: float) -> None:
        from core.components import PhysicsComponent
        phys = self.owner.get_component(PhysicsComponent)

        if self._freeze_timer > 0:
            self._freeze_timer -= dt
            if self._freeze_timer <= 0 and phys:
                # Freeze done — launch knockback
                phys.velocity = Vec2(self.knockback_velocity.x, self.knockback_velocity.y)
                phys.is_grounded = False

        if self._stun_timer > 0:
            self._stun_timer -= dt
            if self._stun_timer <= 0 and phys:
                phys.immovable = False

    @property
    def is_in_hitstun(self) -> bool:
        return self._stun_timer > 0
