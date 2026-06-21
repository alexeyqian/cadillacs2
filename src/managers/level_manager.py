"""
managers/level_manager.py
==========================
LevelManager, StageManager, WaveManager.
Data types (SpawnEntry, WaveData, StageData, LevelData) live in data/level_data.py.
GameSession lives in game_session.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.primitives import Rect2, Vec2
from data.level_data import StageData, WaveData, SpawnEntry

if TYPE_CHECKING:
    from game_session import GameSession


class LevelManager:
    """
    Owns level-to-level progression.
    Loads LevelData JSON via load_level().
    Delegates to StageManager for the first stage.
    Listens for 'stage:complete' to advance stages or end the level.
    """

    def __init__(self, level_paths: list[str], session: "GameSession") -> None:
        self._levels  = level_paths
        self._session = session
        self._current = None

    def on_attach(self, bus) -> None:
        bus.on("stage:complete", self._on_stage_complete)
        bus.on("level:complete", self._on_level_complete)

    def load_level(self, index: int) -> None:
        from data.level_data import load_level
        path = self._levels[index]
        self._current = load_level(path)
        self._session.event_bus.emit("level:started", {
            "level_id":    self._current.id,
            "music_track": self._current.music_track,
        })
        self._session.stage_manager.load_stage(self._current.stages[0], stage_index=0)

    def _on_stage_complete(self, payload) -> None:
        next_idx = payload["stage_index"] + 1
        if next_idx < len(self._current.stages):
            self._session.stage_manager.load_stage(
                self._current.stages[next_idx], stage_index=next_idx
            )
        else:
            self._session.event_bus.emit("level:complete", {
                "level_id": self._current.id
            })

    def _on_level_complete(self, payload) -> None:
        next_idx = self._session.current_level_index + 1
        if next_idx < len(self._levels):
            self._session.current_level_index = next_idx
            self.load_level(next_idx)
        else:
            self._session.event_bus.emit("game:complete", {})


class StageManager:
    """
    Owns stage-to-wave progression within a level.
    Clears old stage objects, populates platforms and pickups,
    places the player at entry_position, then hands waves to WaveManager.
    """

    def __init__(self, session: "GameSession", wave_manager: "WaveManager") -> None:
        self._session      = session
        self._wave_manager = wave_manager
        self._current:     StageData | None = None
        self._stage_index  = 0

    def on_attach(self, bus) -> None:
        bus.on("wave:complete", self._on_wave_complete)

    def load_stage(self, stage: StageData, stage_index: int = 0) -> None:
        self._current     = stage
        self._stage_index = stage_index

        scene        = self._session.scene
        asset_cache  = self._session.asset_cache

        # Clear everything except the player
        for obj in list(scene.all_objects()):
            if not obj.has_tag("player"):
                scene.destroy(obj)
        scene.update(0)  # flush pending destroys

        # Preload background atlas
        asset_cache.load_atlas(stage.background)

        # Preload atlases for every enemy type that appears in this stage's waves
        from data.enemy_data import ENEMY_REGISTRY
        seen_atlases: set[str] = set()
        for wave in stage.waves:
            for entry in wave.enemies:
                data = ENEMY_REGISTRY.get(entry.enemy_id)
                if data and data.sprite_atlas not in seen_atlases:
                    asset_cache.load_atlas(data.sprite_atlas)
                    seen_atlases.add(data.sprite_atlas)

        # Spawn static pickups
        from objects.pickup import Pickup
        from data.item_data import ITEM_REGISTRY
        for pickup in stage.pickups:
            item = ITEM_REGISTRY.get(pickup.item_id)
            if item:
                scene.spawn(Pickup(
                    f"pickup_{pickup.item_id}_{pickup.x}_{pickup.y}",
                    item,
                    Vec2(pickup.x, pickup.y),
                ))

        # Place player at stage entry
        player = self._session.player
        if player:
            player.position = Vec2(stage.entry_position.x, stage.entry_position.y)

        # Hand waves to WaveManager and emit stage started
        self._wave_manager.load_stage_waves(stage.waves)
        self._session.event_bus.emit("stage:started", {
            "stage_id":             stage.id,
            "stage_index":          stage_index,
            "background":           stage.background,
            "music_track_override": stage.music_track_override,
            "scroll_limit_x":       stage.scroll_limit_x,
            "ground_y_min":         stage.ground_y_min,
            "ground_y_max":         stage.ground_y_max,
        })

    def _on_wave_complete(self, payload) -> None:
        self._session.event_bus.emit("camera:unlock", {
            "stage_index": self._stage_index
        })
        if payload.get("all_waves_done"):
            self._session.event_bus.emit("stage:complete", {
                "stage_index": self._stage_index
            })


class WaveManager:
    """
    Watches trigger conditions each update tick.
    Spawns enemies (with optional stagger) when a trigger fires.
    Tracks kills via 'object:died'; emits 'wave:complete' when cleared.
    """

    def __init__(self, session: "GameSession", enemy_factory) -> None:
        self._session       = session
        self._enemy_factory = enemy_factory
        self._waves:        list[WaveData] = []
        self._current_wave  = 0
        self._alive:        set[str] = set()
        self._elapsed       = 0.0
        self._stagger_queue: list[tuple[float, SpawnEntry]] = []  # (spawn_at_time, entry)

    def on_attach(self, bus) -> None:
        bus.on("object:died", self._on_enemy_died)

    def load_stage_waves(self, waves: list[WaveData]) -> None:
        self._waves        = waves
        self._current_wave = 0
        self._alive.clear()
        self._elapsed      = 0.0
        self._stagger_queue.clear()

    def update(self, dt: float) -> None:
        self._elapsed += dt

        # Flush stagger queue
        ready = [(t, e) for t, e in self._stagger_queue if self._elapsed >= t]
        for t, entry in ready:
            self._stagger_queue.remove((t, entry))
            self._do_spawn(entry)

        if self._current_wave >= len(self._waves):
            return

        wave = self._waves[self._current_wave]
        players = self._session.scene.find_by_tag("player")

        if self._check_trigger(wave, players):
            self._spawn_wave(wave)

    def _check_trigger(self, wave: WaveData, players: list) -> bool:
        t = wave.trigger
        if t == "on_stage_start":
            return True
        if t.startswith("on_enter_x:"):
            x = float(t.split(":")[1])
            return any(p.position.x >= x for p in players)
        if t.startswith("on_timer:"):
            return self._elapsed >= float(t.split(":")[1])
        return False

    def _spawn_wave(self, wave: WaveData) -> None:
        if wave.camera_lock_x is not None:
            self._session.event_bus.emit("camera:lock", {
                "limit_x": wave.camera_lock_x
            })

        for i, entry in enumerate(wave.enemies):
            spawn_at = self._elapsed + i * wave.spawn_stagger
            self._stagger_queue.append((spawn_at, entry))

        # Mark wave consumed so trigger doesn't re-fire
        wave.trigger = "__spawned__"

    def _do_spawn(self, entry: SpawnEntry) -> None:
        enemy = self._enemy_factory.create(entry.enemy_id, Vec2(entry.x, entry.y))
        if not entry.facing_right:
            enemy.animation.set_facing(False)
        self._alive.add(enemy.id)
        self._session.scene.spawn(enemy)

    def _on_enemy_died(self, payload) -> None:
        obj = payload.get("object")
        if obj and obj.id in self._alive:
            self._alive.discard(obj.id)
            if not self._alive and not self._stagger_queue:
                self._advance_wave()

    def _advance_wave(self) -> None:
        self._current_wave += 1
        all_done = self._current_wave >= len(self._waves)
        self._session.event_bus.emit("wave:complete", {
            "wave_index":     self._current_wave - 1,
            "all_waves_done": all_done,
        })
