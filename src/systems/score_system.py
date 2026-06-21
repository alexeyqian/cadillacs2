"""
systems/score_system.py
========================
Listens to combat events; maintains score independently of Player.
"""

from __future__ import annotations

from core.game_object import Scene


class ScoreSystem:
    """
    Subscribes to:
        damage:dealt → base points
        object:died  → kill bonus
        combo:hit    → multiplier applied

    Emits:
        score:changed → HUD, SaveManager
    """

    def __init__(self) -> None:
        self.score: int = 0
        self.high_score: int = 0
        self._bus = None

    def on_attach(self, bus) -> None:
        self._bus = bus
        bus.on("damage:dealt", self._on_damage_dealt)
        bus.on("object:died",  self._on_enemy_died)

    def _on_damage_dealt(self, payload) -> None:
        if payload.get("instigator") and payload["instigator"].has_tag("player"):
            pts = int(payload.get("amount", 0))
            self._add(pts)

    def _on_enemy_died(self, payload) -> None:
        obj = payload.get("object")
        if obj and obj.has_tag("enemy"):
            bonus = getattr(obj, "xp_reward", 50)
            self._add(bonus * 2)

    def _add(self, delta: int) -> None:
        self.score += delta
        self.high_score = max(self.high_score, self.score)
        if self._bus:
            self._bus.emit("score:changed", {"score": self.score, "delta": delta})

    def reset(self) -> None:
        self.score = 0

    def update(self, dt: float, scene: Scene) -> None:
        pass
