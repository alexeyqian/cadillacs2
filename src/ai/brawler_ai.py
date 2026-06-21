"""
ai/brawler_ai.py
=================
Walk toward the nearest player. Attack when in range.
Classic grunt AI.
"""

from __future__ import annotations

from core.player_enemy import AIStrategy
from core.primitives import Vec2


class BrawlerAI(AIStrategy):
    """
    States: idle → chase → attack → recover → chase
    Aggro: always active (no perception check).
    """

    def __init__(self, aggro_range: float = 400.0, attack_range: float = 60.0) -> None:
        self.aggro_range   = aggro_range
        self.attack_range  = attack_range
        self._state        = "idle"
        self._recover_timer= 0.0

    def on_attach(self, enemy) -> None:
        self._state = "chase"

    def update(self, dt: float, enemy) -> None:
        if not enemy.is_alive:
            return
        if enemy.scene is None:
            return

        players = [p for p in enemy.scene.find_by_tag("player") if getattr(p, "is_alive", True)]
        if not players:
            return

        # Target nearest player
        target = min(players, key=lambda p: self._dist(enemy.position, p.position))
        dist   = self._dist(enemy.position, target.position)
        dx     = target.position.x - enemy.position.x

        if self._recover_timer > 0:
            self._recover_timer -= dt
            return

        if dist <= self.attack_range:
            if not enemy.combat.is_attacking:
                enemy.attack("punch")
                self._recover_timer = 0.3
        elif dist <= self.aggro_range:
            enemy.move(Vec2(1.0 if dx > 0 else -1.0, 0.0))
        else:
            enemy.move(Vec2(0.0, 0.0))

    @staticmethod
    def _dist(a: Vec2, b: Vec2) -> float:
        import math
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
