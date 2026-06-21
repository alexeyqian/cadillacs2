"""
game_session.py
===============
GameSession — owns everything that survives stage and level transitions:
player, scene, event bus, score, lives, and all manager references.

Created once when a new game starts. Passed by reference into every manager
so they share a single source of truth without using globals.

Step 3 will flesh out __init__ and the update/draw wiring.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.primitives import EventBus
from core.game_object import Scene

if TYPE_CHECKING:
    from core.player_enemy import Player
    from managers.level_manager import LevelManager, StageManager, WaveManager


class GameSession:
    """
    Single container for all cross-cutting runtime state.

    Attributes set by Step 3 (GameSession.__init__):
        player               — the human-controlled Player instance
        scene                — single Scene, lives for the whole game
        event_bus            — shared EventBus, injected into all managers
        score                — running score
        lives                — remaining lives
        current_level_index  — index into LevelManager._levels
        current_stage_index  — index into the current LevelData.stages

    Manager references (set after managers are constructed):
        level_manager
        stage_manager
        wave_manager
    """

    player:              "Player | None"
    scene:               Scene
    event_bus:           EventBus
    score:               int
    lives:               int
    current_level_index: int
    current_stage_index: int
    level_manager:       "LevelManager | None"
    stage_manager:       "StageManager | None"
    wave_manager:        "WaveManager | None"
