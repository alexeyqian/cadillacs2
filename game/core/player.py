"""
player_enemy.py
===============
Player — human-controlled Character.
Enemy  — AI-controlled Character.

No IInputProvider or IAIStrategy abstract base classes.
Both are plain base classes with no-op default methods.
Subclass and override — Python duck-typing handles the rest.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .character import AttackDef, Character
from .component_base import ComponentBase
from .components import CharacterStats, DamageInfo
from .primitives import Vec2

if TYPE_CHECKING:
    from .game_object import Scene


# ────────────────────────────────────────────────────────────
#  PLAYER
# ────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────
# InputProvider — plain base class, not ABC.
# Subclass and override get_axis / is_action_just_pressed
# for keyboard, gamepad, replay buffer, or AI controller.
# ─────────────────────────────────────────────

class InputProvider:
    """
    Base input source. Default implementations return neutral values
    so partial overrides are safe (e.g. a test stub that only overrides
    is_action_just_pressed).
    """

    def get_axis(self, axis: str) -> float:
        """Normalised axis in [-1, 1]. axis: 'horizontal' | 'vertical'."""
        return 0.0

    def is_action_pressed(self, action: str) -> bool:
        """True while the action button is held."""
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        """True only on the first frame the button is pressed."""
        return False


# ─────────────────────────────────────────────
# InventoryComponent — player-exclusive
# ─────────────────────────────────────────────

@dataclass
class PickupItem:
    id: str
    name: str
    quantity: int
    use: Callable[["Player"], None]


class InventoryComponent(ComponentBase):
    """Item bag. Only Player carries items."""

    def __init__(self) -> None:
        self._items: dict[str, PickupItem] = {}

    def update(self, dt: float) -> None:
        pass

    def add_item(self, item: PickupItem) -> None:
        import copy
        existing = self._items.get(item.id)
        if existing:
            existing.quantity += item.quantity
        else:
            self._items[item.id] = copy.copy(item)

    def remove_item(self, item_id: str, amount: int = 1) -> bool:
        item = self._items.get(item_id)
        if item is None or item.quantity < amount:
            return False
        item.quantity -= amount
        if item.quantity == 0:
            del self._items[item_id]
        return True

    def use_item(self, item_id: str) -> bool:
        item = self._items.get(item_id)
        if item is None:
            return False
        item.use(self.owner)  # type: ignore[arg-type]
        self.remove_item(item_id)
        return True

    def has_item(self, item_id: str) -> bool:
        return item_id in self._items

    def get_all(self) -> list[PickupItem]:
        return list(self._items.values())


# ─────────────────────────────────────────────
# ExperienceComponent — player-exclusive
# ─────────────────────────────────────────────

class ExperienceComponent(ComponentBase):
    """XP and level tracking. Override xp_for_level() for custom curves."""

    def __init__(self) -> None:
        self.level: int = 1
        self.current_xp: int = 0
        self.on_level_up: Callable[[int], None] | None = None

    def update(self, dt: float) -> None:
        pass

    def xp_for_level(self, level: int) -> int:
        return level * 100

    def add_xp(self, amount: int) -> None:
        self.current_xp += amount
        while self.current_xp >= self.xp_for_level(self.level):
            self.current_xp -= self.xp_for_level(self.level)
            self.level += 1
            if self.on_level_up:
                self.on_level_up(self.level)


# ─────────────────────────────────────────────
# Player
# ─────────────────────────────────────────────

class Player(Character):
    """
    Human-controlled Character.

    Input is injected via InputProvider — Player never reads raw
    keyboard/gamepad state directly. This enables:
      - Local co-op   (one InputProvider per player slot)
      - Replay system (record/playback InputProvider)
      - Test stubs    (scripted InputProvider)
    """

    def __init__(
        self,
        entity_id: str,
        player_index: int,
        input_provider: InputProvider,
        stats: CharacterStats,
        max_health: int,
    ) -> None:
        super().__init__(entity_id, f"Player{player_index + 1}", stats, max_health)
        self.player_index = player_index
        self.input = input_provider
        self.score: int = 0

        self.add_tag("player")

        self._inventory  = InventoryComponent()
        self._experience = ExperienceComponent()
        self.add_component(self._inventory).add_component(self._experience)

        self._wire_callbacks()

    def _wire_callbacks(self) -> None:
        def _on_hit(atk: AttackDef, _target: Character) -> None:
            self.score += 10 * self.combat.combo_count

        self.combat.on_hit_landed = _on_hit

    @property
    def inventory(self) -> InventoryComponent:
        return self._inventory

    @property
    def experience(self) -> ExperienceComponent:
        return self._experience

    def update(self, dt: float) -> None:
        self._process_input()
        super().update(dt)

    def _process_input(self) -> None:
        if not self.is_alive:
            return
        h = self.input.get_axis("horizontal")
        v = self.input.get_axis("vertical")
        self.move(Vec2(h, v))

        if self.input.is_action_just_pressed("jump"):
            self.jump()
        if self.input.is_action_just_pressed("attack_light"):
            self.attack("light")
        if self.input.is_action_just_pressed("attack_heavy"):
            self.attack("heavy")
        if self.input.is_action_just_pressed("use_item"):
            self.inventory.use_item("health_potion")

    def grant_xp(self, amount: int) -> None:
        self._experience.add_xp(amount)

