from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .component_base import ComponentBase
from .primitives import Rect2, Vec2

if TYPE_CHECKING:
    from .game_object import GameObject

# ─────────────────────────────────────────────
# StatsComponent
# ─────────────────────────────────────────────

@dataclass
class CharacterStats:
    move_speed: float = 220.0       # px/s
    jump_force: float = 550.0       # initial upward velocity
    attack_power: float = 1.0       # damage multiplier
    defense: float = 0.0            # damage reduction 0.0–1.0
    recovery_frames: int = 8        # frames before next action after a whiff


class StatsComponent(ComponentBase):
    """
    Base stats plus additive bonuses from buffs, equipment, or level-ups.
    Use get() for the effective value in combat calculations.
    """

    def __init__(self, base: CharacterStats) -> None:
        import copy
        self.base: CharacterStats = copy.copy(base)
        self.bonuses: dict[str, float] = {}

    def get(self, stat: str) -> float:
        return float(getattr(self.base, stat, 0.0)) + self.bonuses.get(stat, 0.0)

    def update(self, dt: float) -> None:
        pass   # ticked by buff/debuff system if needed