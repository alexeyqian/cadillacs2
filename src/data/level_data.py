"""
data/level_data.py
==================
Pure dataclasses for the Level → Stage → Wave → SpawnEntry hierarchy.
No game logic, no imports from managers or systems.
Loaded from JSON by load_level(); consumed by LevelManager / StageManager.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from core.primitives import Vec2


@dataclass
class SpawnEntry:
    """One enemy instance to place when its parent wave triggers."""
    enemy_id:     str
    x:            float
    y:            float
    facing_right: bool = False


@dataclass
class WaveData:
    """
    A group of enemies that spawn together under one trigger condition.

    trigger formats:
        "on_enter_x:<value>"  — fires when player's x >= value
        "on_stage_start"      — fires immediately when the stage loads

    camera_lock_x:   camera stops scrolling right past this x until cleared.
    spawn_stagger:   seconds between each consecutive enemy spawn (0 = all at once).
    unlock_on_clear: camera unlocks and player may advance when all enemies die.
    """
    trigger:         str
    enemies:         list[SpawnEntry] = field(default_factory=list)
    camera_lock_x:   float | None     = None
    unlock_on_clear: bool             = True
    spawn_stagger:   float            = 0.0

    @classmethod
    def from_dict(cls, d: dict) -> "WaveData":
        return cls(
            trigger         = d["trigger"],
            camera_lock_x   = d.get("camera_lock_x"),
            unlock_on_clear = d.get("unlock_on_clear", True),
            spawn_stagger   = d.get("spawn_stagger", 0.0),
            enemies=[
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
class PickupPlacement:
    """A single pickup item placed in a stage (from the [item_id, x, y] JSON format)."""
    item_id: str
    x:       float
    y:       float


@dataclass
class StageData:
    """
    One self-contained arena section within a level.
    The scene is cleared of non-player objects each time a new stage loads.
    """
    id:                   str
    display_name:         str
    background:           str       # e.g. "content/backgrounds/docks_01.png"
    entry_position:       Vec2      # where the player is placed on stage load
    exit_position:        Vec2      # where the exit trigger is placed
    scroll_limit_x:       float     # hard camera scroll limit for this stage
    ground_y_min:         float                 = 0.0
    ground_y_max:         float                 = 120.0
    waves:                list[WaveData]        = field(default_factory=list)
    pickups:              list[PickupPlacement] = field(default_factory=list)
    music_track_override: str | None            = None


@dataclass
class LevelData:
    """Top-level descriptor for one level, loaded from a single JSON file."""
    id:            str
    display_name:  str
    music_track:   str
    stages:        list[StageData] = field(default_factory=list)
    next_level_id: str | None      = None


def load_level(path: str | Path) -> LevelData:
    """Parse a level JSON file into a fully typed LevelData tree."""
    with open(path) as f:
        raw = json.load(f)

    stages: list[StageData] = []
    for s in raw.get("stages", []):
        ep = s["entry_position"]
        xp = s["exit_position"]
        stages.append(StageData(
            id                   = s["id"],
            display_name         = s["display_name"],
            background           = s["background"],
            entry_position       = Vec2(ep["x"], ep["y"]),
            exit_position        = Vec2(xp["x"], xp["y"]),
            scroll_limit_x       = s["scroll_limit_x"],
            ground_y_min         = float(s.get("ground_y_min", 0.0)),
            ground_y_max         = float(s.get("ground_y_max", 120.0)),
            waves                = [WaveData.from_dict(w) for w in s.get("waves", [])],
            pickups              = [
                PickupPlacement(item_id=p[0], x=p[1], y=p[2])
                for p in s.get("pickups", [])
            ],
            music_track_override = s.get("music_track_override"),
        ))

    return LevelData(
        id            = raw["id"],
        display_name  = raw["display_name"],
        music_track   = raw["music_track"],
        stages        = stages,
        next_level_id = raw.get("next_level_id"),
    )
