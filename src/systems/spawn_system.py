"""
systems/spawn_system.py
========================
Reads LevelData.waves and spawns enemies when trigger conditions are met.
"""

from __future__ import annotations

from core.game_object import Scene
from core.primitives import Vec2


class SpawnSystem:
    """
    Trigger condition types:
        'on_enter_x:{value}'    — player passes x coordinate
        'on_wave_clear:{index}' — previous wave fully defeated
        'on_timer:{seconds}'    — elapsed time since level start
    """

    def __init__(self) -> None:
        self._waves: list = []
        self._current_wave: int = 0
        self._wave_enemy_ids: set[str] = set()
        self._elapsed: float = 0.0
        self._enemy_factory = None

    def load(self, level_data, enemy_factory) -> None:
        from data.level_data import LevelData
        self._waves = level_data.waves
        self._enemy_factory = enemy_factory
        self._current_wave = 0
        self._wave_enemy_ids.clear()
        self._elapsed = 0.0

    def on_attach(self, bus) -> None:
        bus.on("object:died", self._on_enemy_died)

    def _on_enemy_died(self, payload) -> None:
        obj = payload.get("object")
        if obj and obj.id in self._wave_enemy_ids:
            self._wave_enemy_ids.discard(obj.id)

    @property
    def current_wave_cleared(self) -> bool:
        return len(self._wave_enemy_ids) == 0

    def update(self, dt: float, scene: Scene) -> None:
        self._elapsed += dt
        players = scene.find_by_tag("player")

        for i, wave in enumerate(self._waves):
            if wave.get("_spawned"):
                continue
            if self._check_trigger(wave["trigger"], i, players):
                self._spawn_wave(wave, scene)
                wave["_spawned"] = True

    def _check_trigger(self, trigger: str, wave_idx: int, players: list) -> bool:
        if trigger.startswith("on_enter_x:"):
            x = float(trigger.split(":")[1])
            return any(p.position.x >= x for p in players)
        if trigger.startswith("on_wave_clear:"):
            idx = int(trigger.split(":")[1])
            if idx == 0:
                return self.current_wave_cleared
            prev = self._waves[idx - 1]
            return prev.get("_spawned") and self.current_wave_cleared
        if trigger.startswith("on_timer:"):
            t = float(trigger.split(":")[1])
            return self._elapsed >= t
        return False

    def _spawn_wave(self, wave: dict, scene: Scene) -> None:
        if self._enemy_factory is None:
            return
        for entry in wave.get("entries", []):
            enemy = self._enemy_factory.create(
                entry["enemy_id"],
                Vec2(entry["x"], entry["y"]),
            )
            self._wave_enemy_ids.add(enemy.id)
            scene.spawn(enemy)
