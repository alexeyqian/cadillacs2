"""
data/level_data.py
==================
LevelData and WaveEntry dataclasses. Loaded from JSON by LevelManager.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WaveEntry:
    """
    trigger examples:
        'on_enter_x:400'   — player reaches x=400
        'on_wave_clear:0'  — wave 0 is cleared
        'on_timer:10.0'    — 10 seconds into the level
    """
    trigger: str
    entries: list[dict] = field(default_factory=list)


@dataclass
class LevelData:
    id: str
    display_name: str
    background_layers: list[str]
    music_track: str
    platforms: list[dict]          # [{"x":0,"y":400,"width":800,"height":32,"one_way":false}]
    waves: list[dict]              # raw dicts; SpawnSystem hydrates
    pickups: list                  # [[item_id, x, y], ...]
    exit_position: dict            # {"x":750,"y":300}
    next_level_id: str | None = None
