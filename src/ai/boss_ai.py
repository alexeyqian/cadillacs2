"""
ai/boss_ai.py
=============
Phase-based boss AI. Calls trigger_phase_transition() at HP thresholds.
"""

from __future__ import annotations

from core.player_enemy import AIStrategy
from core.primitives import Vec2
from ai.brawler_ai import BrawlerAI
from ai.ranged_ai import RangedAI


class BossAI(AIStrategy):
    """
    Phase 1 (HP > 50%): aggressive brawler.
    Phase 2 (HP 25–50%): brawler + ranged attacks.
    Phase 3 (HP < 25%): enraged — speed boost, ranged + melee.
    """

    def __init__(self) -> None:
        self._phase = 1
        self._inner: AIStrategy = BrawlerAI(aggro_range=500, attack_range=70)

    def on_attach(self, enemy) -> None:
        self._inner.on_attach(enemy)

    def update(self, dt: float, enemy) -> None:
        if not enemy.is_alive:
            return

        pct = enemy.health.health_percent

        if self._phase == 1 and pct <= 0.5:
            self._phase = 2
            new_strategy = RangedAI(preferred_dist=180, throw_range=350, throw_cooldown=1.0)
            enemy.trigger_phase_transition(new_strategy, stat_bonuses={"move_speed": 40.0})
            self._inner = new_strategy
            self._inner.on_attach(enemy)

        elif self._phase == 2 and pct <= 0.25:
            self._phase = 3
            new_strategy = BrawlerAI(aggro_range=600, attack_range=80)
            enemy.trigger_phase_transition(
                new_strategy,
                stat_bonuses={"move_speed": 60.0, "attack_power": 0.5}
            )
            self._inner = new_strategy
            self._inner.on_attach(enemy)

        self._inner.update(dt, enemy)
