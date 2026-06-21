"""
ai/ranged_ai.py
================
Maintain distance from the player; throw projectiles when in range.
"""

from __future__ import annotations

from core.player_enemy import AIStrategy
from core.primitives import Vec2


class RangedAI(AIStrategy):

    def __init__(
        self,
        preferred_dist: float = 200.0,
        throw_range: float = 300.0,
        throw_cooldown: float = 1.5,
    ) -> None:
        self.preferred_dist = preferred_dist
        self.throw_range    = throw_range
        self.throw_cooldown = throw_cooldown
        self._cooldown      = 0.0

    def on_attach(self, enemy) -> None:
        self._cooldown = 1.0   # brief delay before first shot

    def update(self, dt: float, enemy) -> None:
        if not enemy.is_alive or enemy.scene is None:
            return
        if self._cooldown > 0:
            self._cooldown -= dt

        players = [p for p in enemy.scene.find_by_tag("player") if getattr(p, "is_alive", True)]
        if not players:
            return

        target = min(players, key=lambda p: self._dist(enemy.position, p.position))
        dist   = self._dist(enemy.position, target.position)
        dx     = target.position.x - enemy.position.x

        # Maintain preferred distance
        if dist < self.preferred_dist - 30:
            enemy.move(Vec2(-1.0 if dx > 0 else 1.0, 0.0))
        elif dist > self.preferred_dist + 30:
            enemy.move(Vec2(1.0 if dx > 0 else -1.0, 0.0))
        else:
            enemy.move(Vec2(0.0, 0.0))

        # Throw projectile
        if dist <= self.throw_range and self._cooldown <= 0:
            self._throw(enemy, target)
            self._cooldown = self.throw_cooldown

    def _throw(self, enemy, target) -> None:
        from objects.projectile import Projectile
        import math, uuid
        dx = target.position.x - enemy.position.x
        dy = target.position.y - enemy.position.y
        dist = math.sqrt(dx * dx + dy * dy) or 1
        speed = 300.0
        vel = Vec2(dx / dist * speed, dy / dist * speed)
        proj = Projectile(
            str(uuid.uuid4()), enemy, vel,
            damage=enemy.stats.get("attack_power") * 8,
            ttl=2.0,
        )
        proj.position = Vec2(enemy.position.x, enemy.position.y)
        if enemy.scene:
            enemy.scene.spawn(proj)

    @staticmethod
    def _dist(a, b) -> float:
        import math
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
