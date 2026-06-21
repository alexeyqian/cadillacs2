"""
objects/projectile.py
=====================
Owned by a Character; constant velocity; self-destructs on TTL or wall hit.
"""

from __future__ import annotations

from core.game_object import GameObject, Scene
from core.character import Character
from core.primitives import Vec2


class Projectile(GameObject):
    """
    Has one permanently active HitboxDef for its lifetime.
    source stored so CollisionSystem can attribute damage correctly.
    """

    def __init__(
        self,
        entity_id: str,
        source: Character,
        velocity: Vec2,
        damage: float,
        ttl: float = 2.0,
    ) -> None:
        super().__init__(entity_id, "Projectile")
        self.source   = source
        self.velocity = velocity
        self.damage   = damage
        self.ttl      = ttl
        self._elapsed = 0.0
        self.add_tag("projectile")
        self.add_tag("renderable")
        self.transform.z_index = 2   # Z_PROJECTILE

    def update(self, dt: float) -> None:
        self._elapsed += dt
        if self._elapsed >= self.ttl:
            if self.scene:
                self.scene.destroy(self)
            return
        self.prev_position = Vec2(self.position.x, self.position.y)
        self.position.x += self.velocity.x * dt
        self.position.y += self.velocity.y * dt
