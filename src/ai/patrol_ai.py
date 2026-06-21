"""
ai/patrol_ai.py
================
Walk back and forth between two x positions.
Aggro when a player enters vision cone; switches to BrawlerAI behaviour.
"""

from __future__ import annotations

from core.player_enemy import AIStrategy
from core.primitives import Vec2


class PatrolAI(AIStrategy):

    def __init__(
        self,
        left_x: float = 0.0,
        right_x: float = 200.0,
        attack_range: float = 60.0,
    ) -> None:
        self.left_x      = left_x
        self.right_x     = right_x
        self.attack_range= attack_range
        self._dir        = 1.0   # 1 = right, -1 = left
        self._aggroed    = False
        self._target     = None

    def on_attach(self, enemy) -> None:
        self._dir = 1.0

    def update(self, dt: float, enemy) -> None:
        if not enemy.is_alive or enemy.scene is None:
            return

        players = [p for p in enemy.scene.find_by_tag("player") if getattr(p, "is_alive", True)]

        # Check aggro via PerceptionComponent
        perc = enemy.perception
        for player in players:
            if perc.can_see(player.position, enemy.position, enemy.facing_right):
                self._aggroed = True
                self._target  = player
                break

        if self._aggroed and self._target:
            dist = self._dist(enemy.position, self._target.position)
            dx   = self._target.position.x - enemy.position.x
            if dist <= self.attack_range:
                if not enemy.combat.is_attacking:
                    enemy.attack("punch")
            else:
                enemy.move(Vec2(1.0 if dx > 0 else -1.0, 0.0))
        else:
            # Patrol
            enemy.move(Vec2(self._dir, 0.0))
            if enemy.position.x >= self.right_x:
                self._dir = -1.0
            elif enemy.position.x <= self.left_x:
                self._dir = 1.0

    @staticmethod
    def _dist(a, b) -> float:
        import math
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
