from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .component_base import ComponentBase
from .primitives import Rect2, Vec2

if TYPE_CHECKING:
    from .game_object import GameObject


# ─────────────────────────────────────────────
# HealthComponent
# ─────────────────────────────────────────────

@dataclass
class DamageInfo:
    amount: float               # raw value before defense reduction; float is fine here
    damage_type: str = "physical"
    source: "GameObject | None" = None
    knockback: Vec2 = field(default_factory=Vec2)


class HealthComponent(ComponentBase):
    """
    Manages hit points, shield absorption, and post-hit invincibility frames.

    HP is int — "150 hit points" is a discrete quantity.
    DamageInfo.amount is float because raw damage often involves float
    multipliers (e.g. 10 * 1.5 * 0.8). The conversion to int happens
    inside take_damage() once all reductions are applied, using math.floor
    (always rounds down, favouring the defender).

    take_damage() returns int — the settled, discrete HP removed.
    Callers use this for score, lifesteal, screen-shake intensity, etc.
    """

    def __init__(self, max_health: int, invincibility_duration: float = 0.1) -> None:
        self.max_health: int = max_health
        self.current_health: int = max_health
        self.invincibility_duration: float = invincibility_duration
        self._invincibility_timer: float = 0.0

        self.max_shield: int = 0
        self.current_shield: int = 0

        self.on_damage: Callable[[DamageInfo, int], None] | None = None
        self.on_death: Callable[[DamageInfo], None] | None = None
        self.on_heal: Callable[[int, int], None] | None = None

    @property
    def is_alive(self) -> bool:
        return self.current_health > 0

    @property
    def is_invincible(self) -> bool:
        return self._invincibility_timer > 0

    @property
    def health_percent(self) -> float:
        return self.current_health / self.max_health

    def update(self, dt: float) -> None:
        if self._invincibility_timer > 0:
            self._invincibility_timer -= dt

    def take_damage(self, info: DamageInfo) -> int:
        """
        Apply damage and return the actual HP removed (int).
        Returns 0 if the target is dead or currently invincible.
        Rounding: math.floor — fractional damage always rounds down.
        """
        if not self.is_alive or self.is_invincible:
            return 0

        dmg: float = info.amount

        # Shield absorbs before HP
        if self.current_shield > 0:
            absorbed = min(float(self.current_shield), dmg)
            self.current_shield -= math.floor(absorbed)
            dmg -= absorbed

        # Convert to discrete HP once all float arithmetic is done
        hp_removed: int = min(math.floor(dmg), self.current_health)
        self.current_health -= hp_removed
        self._invincibility_timer = self.invincibility_duration

        if self.on_damage:
            self.on_damage(info, hp_removed)

        scene = self.owner.scene if hasattr(self, "owner") else None
        if scene:
            scene.event_bus.emit("damage:taken", {
                "target": self.owner,
                "amount": hp_removed,
                "source": info.source,
            })

        if not self.is_alive:
            if self.on_death:
                self.on_death(info)
            if scene:
                scene.event_bus.emit("object:died", {
                    "object": self.owner,
                    "killed_by": info.source,
                })

        return hp_removed

    def heal(self, amount: int) -> int:
        """Restore HP. Returns the actual amount healed (capped at max)."""
        actual = min(amount, self.max_health - self.current_health)
        self.current_health += actual
        if self.on_heal:
            self.on_heal(actual, self.current_health)
        return actual

