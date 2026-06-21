"""
managers/level_manager.py
==========================
Loads LevelData from JSON, populates the scene, manages level transitions.
"""

from __future__ import annotations

from dataclasses import dataclass

import json
from core.game_object import Scene
from core.primitives import Rect2, Vec2, EventBus
from core.player_enemy import Player

class GameSession:
    """
    Created once when the player starts a new game or continues.
    Owns everything that must survive stage transitions.
    """
    player: Player            # ← player lives here
    score: int
    lives: int
    current_level_index: int
    current_stage_index: int
    event_bus: EventBus
    scene: Scene              # ← single scene, lives here too

# data/level_data.py

@dataclass
class SpawnEntry:
    """
    One enemy to spawn as part of a wave.
    Pure data — no behaviour, no references to runtime objects.
    """
    enemy_id:     str        # key into ENEMY_REGISTRY e.g. "grunt", "heavy", "boss"
    x:            float      # world-space spawn position
    y:            float      # world-space spawn position
    facing_right: bool = False  # which direction the enemy faces on spawn

@dataclass
class WaveData:
    trigger: str              # "on_enter_x:400" | "on_wave_clear:0"
    enemies: list[SpawnEntry] # what spawns and where
    camera_lock_x: float      # camera stops here until wave cleared
    unlock_on_clear: bool     # advance camera when all enemies dead
    spawn_stagger:   float = 0.0   # seconds between each enemy spawning in the wave

    @classmethod
    def from_dict(cls, d: dict) -> "WaveData":
        return cls(
            trigger         = d["trigger"],
            camera_lock_x   = d["camera_lock_x"],
            unlock_on_clear = d.get("unlock_on_clear", True),
            spawn_stagger   = d.get("spawn_stagger", 0.0),
            enemies         = [
                SpawnEntry(
                    enemy_id     = e["enemy_id"],
                    x            = e["x"],
                    y            = e["y"],
                    facing_right = e.get("facing_right", False),
                )
                for e in d.get("enemies", [])
            ],
        )

@dataclass
class StageData:
    id: str
    background: str          # "docks_bg.png"
    platforms: list[dict]
    waves: list[WaveData]    # ← a stage owns multiple waves
    scroll_limit_x: float    # camera stops scrolling until wave is cleared
    exit_position: Vec2

@dataclass
class LevelData:
    id: str
    display_name: str        # "The Docks"
    stages: list[StageData]  # ← a level owns multiple stages
    music_track: str

class LevelManager:
    """
    Owns level-to-level progression.
    Loads LevelData JSON.
    Signals StageManager to load the first stage.
    Listens for 'stage:complete' to advance or end the level.
    """

    def __init__(self, level_paths: list[str], session: GameSession) -> None:
        self._levels    = level_paths
        self._session   = session
        self._current: LevelData | None = None

    def load_level(self, index: int) -> None:
        path = self._levels[index]
        with open(path) as f:
            self._current = LevelData(**json.load(f))
        self._session.stage_manager.load_stage(self._current.stages[0])

    def on_attach(self, bus) -> None:
        bus.on("stage:complete", self._on_stage_complete)
        bus.on("level:complete", self._on_level_complete)

    def _on_stage_complete(self, payload) -> None:
        stage_idx = payload["stage_index"] + 1
        if stage_idx < len(self._current.stages):
            self._session.stage_manager.load_stage(
                self._current.stages[stage_idx]
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
    Destroys old stage objects, populates new ones.
    Signals WaveManager to start the first wave.
    Listens for 'wave:complete' to advance.
    """

    def __init__(self, session: GameSession, wave_manager: "WaveManager") -> None:
        self._session      = session
        self._wave_manager = wave_manager
        self._current: StageData | None = None
        self._stage_index  = 0

    def load_stage(self, stage: StageData, stage_index: int = 0) -> None:
        self._current     = stage
        self._stage_index = stage_index

        scene = self._session.scene

        # Destroy everything except the player
        for obj in list(scene.all_objects()):
            if not obj.has_tag("player"):
                scene.destroy(obj)

        # Force one scene tick to flush pending destroys
        scene.update(0)

        # Spawn platforms
        for p in stage.platforms:
            from objects.platform import Platform
            from core.primitives import Rect2
            scene.spawn(Platform(
                f"plat_{p['x']}_{p['y']}",
                Rect2(p["x"], p["y"], p["width"], p["height"]),
                p.get("one_way", False),
            ))

        # Place player at stage entry
        player = self._session.player
        if player:
            player.position = Vec2(
                stage.entry_position.x,
                stage.entry_position.y,
            )

        # Start first wave
        self._wave_manager.load_stage_waves(stage.waves)

        self._session.event_bus.emit("stage:started", {
            "stage_id":    stage.id,
            "stage_index": stage_index,
            "background":  stage.background,
        })

    def on_attach(self, bus) -> None:
        bus.on("wave:complete", self._on_wave_complete)

    def _on_wave_complete(self, payload) -> None:
        # Unlock camera so player can advance to next trigger
        self._session.event_bus.emit("camera:unlock", {
            "stage_index": self._stage_index
        })

        if payload.get("all_waves_done"):
            self._session.event_bus.emit("stage:complete", {
                "stage_index": self._stage_index
            })


class WaveManager:
    """
    Owns the current wave within a stage.
    Watches for trigger conditions; spawns enemies; tracks kills.
    Emits 'wave:complete' when all enemies in the wave are dead.
    Emits 'stage:complete' (via StageManager) when the last wave clears.
    """

    def __init__(self, session: GameSession, enemy_factory) -> None:
        self._session       = session
        self._enemy_factory = enemy_factory
        self._waves:  list[WaveData] = []
        self._current_wave  = 0
        self._alive:  set[str] = set()    # entity ids of living wave enemies
        self._elapsed = 0.0

    def load_stage_waves(self, waves: list[WaveData]) -> None:
        self._waves        = waves
        self._current_wave = 0
        self._alive.clear()
        self._elapsed      = 0.0

    def on_attach(self, bus) -> None:
        bus.on("object:died", self._on_enemy_died)

    def _on_enemy_died(self, payload) -> None:
        obj = payload.get("object")
        if obj and obj.id in self._alive:
            self._alive.discard(obj.id)
            if not self._alive:
                self._advance_wave()

    def _advance_wave(self) -> None:
        self._current_wave += 1
        all_done = self._current_wave >= len(self._waves)
        self._session.event_bus.emit("wave:complete", {
            "wave_index":    self._current_wave - 1,
            "all_waves_done": all_done,
        })

    def update(self, dt: float) -> None:
        self._elapsed += dt
        if self._current_wave >= len(self._waves):
            return

        wave = self._waves[self._current_wave]
        players = self._session.scene.find_by_tag("player")

        if self._check_trigger(wave.trigger, players):
            self._spawn_wave(wave)

    def _check_trigger(self, trigger: str, players: list) -> bool:
        if trigger.startswith("on_enter_x:"):
            x = float(trigger.split(":")[1])
            return any(p.position.x >= x for p in players)
        if trigger.startswith("on_timer:"):
            return self._elapsed >= float(trigger.split(":")[1])
        return False

    def _spawn_wave(self, wave: WaveData) -> None:
        # Lock camera at wave's scroll limit
        self._session.event_bus.emit("camera:lock", {
            "limit_x": wave.camera_lock_x
        })
        scene = self._session.scene
        for entry in wave.enemies:
            enemy = self._enemy_factory.create(
                entry["enemy_id"],
                Vec2(entry["x"], entry["y"]),
            )
            self._alive.add(enemy.id)
            scene.spawn(enemy)
        # Mark wave as spawned so trigger doesn't fire again
        wave.trigger = "__spawned__"