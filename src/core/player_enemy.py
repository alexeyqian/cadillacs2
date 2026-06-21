"""
core/player_enemy.py
====================
Player and Enemy — the two Character subclasses.
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


# ── InputProvider ─────────────────────────────────────────────

class InputProvider:
    """Base input source. Subclass for keyboard, gamepad, replay, AI."""

    def get_axis(self, axis: str) -> float:
        return 0.0

    def is_action_pressed(self, action: str) -> bool:
        return False

    def is_action_just_pressed(self, action: str) -> bool:
        return False


# ── InventoryComponent ────────────────────────────────────────

@dataclass
class PickupItem:
    id: str
    name: str
    quantity: int
    use: Callable[["Player"], None]


class InventoryComponent(ComponentBase):
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


# ── ExperienceComponent ───────────────────────────────────────

class ExperienceComponent(ComponentBase):
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


# ── Player ────────────────────────────────────────────────────

class Player(Character):
    """Human-controlled Character. Input injected via InputProvider."""

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
        self.combat.on_hit_landed = lambda atk, _t: self._on_hit(atk)

    def _on_hit(self, atk: AttackDef) -> None:
        self.score += 10 * self.combat.combo_count

    @property
    def inventory(self) -> InventoryComponent:
        return self._inventory

    @property
    def experience(self) -> ExperienceComponent:
        return self._experience

    def update(self, dt: float) -> None:
        self._process_input()
        super().update(dt)
        self._drive_animation()

    def _drive_animation(self) -> None:
        if not self.is_alive:
            self._animation.play("die")
            return
        if self._combat.is_attacking:
            return  # CombatComponent drives attack animation
        if not self._physics.is_grounded:
            self._animation.play("jump")
        elif abs(self._physics.velocity.x) > 1.0:
            self._animation.play("walk")
        else:
            self._animation.play("idle")

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


# ── AIStrategy ────────────────────────────────────────────────

class AIStrategy:
    """Base AI brain. Null-object default — enemy stands still."""

    def on_attach(self, enemy: "Enemy") -> None:
        pass

    def update(self, dt: float, enemy: "Enemy") -> None:
        pass


# ── DropTableComponent ────────────────────────────────────────

@dataclass
class DropEntry:
    item_id: str
    quantity: int
    probability: float


class DropTableComponent(ComponentBase):
    def __init__(self) -> None:
        self.drops: list[DropEntry] = []

    def update(self, dt: float) -> None:
        pass

    def roll(self) -> list[DropEntry]:
        import random
        return [d for d in self.drops if random.random() < d.probability]


# ── PerceptionComponent ───────────────────────────────────────

class PerceptionComponent(ComponentBase):
    def __init__(self) -> None:
        self.vision_angle: float = math.pi / 3
        self.vision_range: float = 300.0
        self.hearing_range: float = 150.0
        self.detected_targets: set[str] = set()

    def update(self, dt: float) -> None:
        pass

    def can_see(self, target_pos: Vec2, owner_pos: Vec2, facing_right: bool) -> bool:
        dx = target_pos.x - owner_pos.x
        dy = target_pos.y - owner_pos.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > self.vision_range:
            return False
        angle_to_target = math.atan2(dy, dx)
        facing_angle = 0.0 if facing_right else math.pi
        return abs(angle_to_target - facing_angle) <= self.vision_angle


# ── Enemy ─────────────────────────────────────────────────────

class Enemy(Character):
    """AI-controlled Character with hot-swappable strategy."""

    def __init__(
        self,
        entity_id: str,
        enemy_type: str,
        stats: CharacterStats,
        max_health: int,
        xp_reward: int = 50,
    ) -> None:
        super().__init__(entity_id, f"Enemy_{enemy_type}", stats, max_health)
        self.enemy_type = enemy_type
        self.xp_reward  = xp_reward
        self.add_tag("enemy")
        if enemy_type == "boss":
            self.add_tag("boss")
        self._drop_table  = DropTableComponent()
        self._perception  = PerceptionComponent()
        self.add_component(self._drop_table).add_component(self._perception)
        self._ai_strategy: AIStrategy = AIStrategy()
        self.health.on_death = lambda info: self._on_death(info)

    def _on_death(self, info: DamageInfo) -> None:
        self.die()
        self._spawn_drops()

    @property
    def drop_table(self) -> DropTableComponent:
        return self._drop_table

    @property
    def perception(self) -> PerceptionComponent:
        return self._perception

    def set_strategy(self, strategy: AIStrategy) -> None:
        self._ai_strategy = strategy
        strategy.on_attach(self)

    def trigger_phase_transition(
        self,
        strategy: AIStrategy,
        stat_bonuses: dict[str, float] | None = None,
    ) -> None:
        self.set_strategy(strategy)
        if stat_bonuses:
            self.stats.bonuses.update(stat_bonuses)

    def update(self, dt: float) -> None:
        self._ai_strategy.update(dt, self)
        super().update(dt)

    def on_spawn(self, scene: "Scene") -> None:
        super().on_spawn(scene)
        self._ai_strategy.on_attach(self)

    def _spawn_drops(self) -> None:
        if self.scene is None:
            return
        for drop in self._drop_table.roll():
            self.scene.event_bus.emit("pickup:spawned", {
                "source": self,
                "position": Vec2(self.position.x, self.position.y),
                "item_id": drop.item_id,
                "quantity": drop.quantity,
            })
