"""
objects/trigger.py
==================
Zone that emits a named event when a Player enters.
Used for: level exits, cutscene starts, wave unlocks, shop entrances.
"""

from __future__ import annotations

from core.game_object import GameObject
from core.primitives import Rect2, Vec2


class Trigger(GameObject):
    """
    Stateless emitter — acts, then optionally destroys itself.
    SpawnSystem and LevelManager subscribe to the emitted events.
    """

    def __init__(
        self,
        entity_id: str,
        zone: Rect2,
        event_name: str,
        one_shot: bool = True,
    ) -> None:
        super().__init__(entity_id, f"Trigger_{event_name}")
        self.zone       = zone
        self.event_name = event_name
        self.one_shot   = one_shot
        self._fired     = False
        self.position   = Vec2(zone.x, zone.y)
        self.add_tag("trigger")

    def update(self, dt: float) -> None:
        if self._fired or self.scene is None:
            return
        players = self.scene.find_by_tag("player")
        for player in players:
            if self.zone.contains_point(player.position):
                self.scene.event_bus.emit(self.event_name, {"trigger": self, "player": player})
                if self.one_shot:
                    self._fired = True
                    self.scene.destroy(self)
                break
