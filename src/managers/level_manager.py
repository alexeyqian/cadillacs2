"""
managers/level_manager.py
==========================
Loads LevelData from JSON, populates the scene, manages level transitions.
"""

from __future__ import annotations

import json
from core.game_object import Scene
from core.primitives import Rect2, Vec2


class LevelManager:
    """
    Transition sequence:
        1. Emit level:transition:start
        2. Destroy current scene objects
        3. Load next LevelData JSON
        4. Populate new scene (platforms, triggers, pickups)
        5. Emit level:transition:end

    Subscribes to:
        level:exit → begin transition to next level
    """

    def __init__(self, level_paths: list[str]) -> None:
        self.level_paths         = level_paths
        self.current_index       = 0
        self._bus                = None
        self._scene: Scene | None = None
        self._spawn_system       = None
        self._enemy_factory      = None
        self._current_level_data = None
        self._asset_cache        = None

    def on_attach(self, bus, scene: Scene, spawn_system=None, enemy_factory=None) -> None:
        self._bus           = bus
        self._scene         = scene
        self._spawn_system  = spawn_system
        self._enemy_factory = enemy_factory
        bus.on("level:exit", self._on_level_exit)

    def load_current(self) -> None:
        if self.current_index >= len(self.level_paths):
            if self._bus:
                self._bus.emit("level:complete", {"level_id": "all"})
            return
        path = self.level_paths[self.current_index]
        self._load(path)

    def _on_level_exit(self, payload) -> None:
        # Unload previous level's atlases before loading next
        if self._current_level_data and self._asset_cache:
            for atlas in self._current_level_data.required_atlases:
                self._asset_cache.unload(atlas)
        self.current_index += 1
        if self._bus:
            self._bus.emit("level:complete", {"level_id": str(self.current_index - 1)})
        self.load_current()

    def _load(self, path: str) -> None:
        from data.level_data import LevelData, WaveEntry
        try:
            with open(path) as f:
                raw = json.load(f)
        except FileNotFoundError:
            return

        level = LevelData(**raw)

        # Preload all atlases this level needs before spawning anything
        if self._asset_cache:
            self._asset_cache.preload_all(level.required_atlases)

        if self._scene is None:
            return

        # Clear existing dynamic objects (keep players)
        for obj in list(self._scene.all_objects()):
            if not obj.has_tag("player"):
                self._scene.destroy(obj)

        # Spawn platforms
        for p in level.platforms:
            from objects.platform import Platform
            plat = Platform(
                f"plat_{id(p)}",
                Rect2(p["x"], p["y"], p["width"], p["height"]),
                p.get("one_way", False),
            )
            self._scene.spawn(plat)

        # Spawn static pickups
        for item_id, x, y in level.pickups:
            from objects.pickup import Pickup
            from data.item_data import ITEM_REGISTRY
            item = ITEM_REGISTRY.get(item_id)
            if item:
                pickup = Pickup(f"pickup_{item_id}_{x}_{y}", item, Vec2(x, y))
                self._scene.spawn(pickup)

        # Spawn exit trigger
        if level.exit_position:
            from objects.trigger import Trigger
            ex = level.exit_position
            trigger = Trigger(
                "exit_trigger",
                Rect2(ex["x"] - 32, ex["y"] - 64, 64, 128),
                "level:exit",
            )
            self._scene.spawn(trigger)

        # Hand waves to SpawnSystem
        if self._spawn_system and self._enemy_factory:
            self._spawn_system.load(level, self._enemy_factory)
