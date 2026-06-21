
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
#  ENEMY
# ────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────
# AIStrategy — plain base class, not ABC.
# No-op defaults mean you can subclass and override
# only on_attach or only update without boilerplate.
#
# Mirrors:
#   Godot  — NavigationAgent2D + custom _physics_process
#   Unity  — NavMeshAgent + StateMachineBehaviour
#   Unreal — AIController + BehaviorTree
# ─────────────────────────────────────────────

class AIStrategy:
    """
    Base AI brain. Swap at runtime for boss phase transitions.
    Default implementation is a null object — enemy stands still.
    """

    def on_attach(self, enemy: "Enemy") -> None:
        """Called once when assigned to an enemy."""

    def update(self, dt: float, enemy: "Enemy") -> None:
        """Called every frame by Enemy.update()."""


# ─────────────────────────────────────────────
# DropTableComponent
# ─────────────────────────────────────────────

@dataclass
class DropEntry:
    item_id: str
    quantity: int
    probability: float          # 0.0 – 1.0


class DropTableComponent(ComponentBase):
    """What the enemy drops on death."""

    def __init__(self) -> None:
        self.drops: list[DropEntry] = []

    def update(self, dt: float) -> None:
        pass

    def roll(self) -> list[DropEntry]:
        import random
        return [d for d in self.drops if random.random() < d.probability]


# ─────────────────────────────────────────────
# PerceptionComponent
# ─────────────────────────────────────────────

class PerceptionComponent(ComponentBase):
    """
    Vision cone and hearing range checks for AI strategies.
    The PhysicsSystem populates detected_targets each frame.
    """

    def __init__(self) -> None:
        self.vision_angle: float = math.pi / 3     # half-angle (~60° total FOV)
        self.vision_range: float = 300.0
        self.hearing_range: float = 150.0
        self.detected_targets: set[str] = set()    # entity ids

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


# ─────────────────────────────────────────────
# Enemy
# ─────────────────────────────────────────────

class Enemy(Character):
    """
    AI-controlled Character.

    The AI brain is hot-swappable via set_strategy(), making boss
    phase transitions a one-liner: trigger_phase_transition(new_strategy).
    """

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

        self._ai_strategy: AIStrategy = AIStrategy()   # null object by default
        self._wire_callbacks()

    def _wire_callbacks(self) -> None:
        def _on_death(info: DamageInfo) -> None:
            self.die()
            self._spawn_drops()

        self.health.on_death = _on_death

    @property
    def drop_table(self) -> DropTableComponent:
        return self._drop_table

    @property
    def perception(self) -> PerceptionComponent:
        return self._perception

    def set_strategy(self, strategy: AIStrategy) -> None:
        """Replace the AI brain. Safe to call mid-fight."""
        self._ai_strategy = strategy
        strategy.on_attach(self)

    def trigger_phase_transition(
        self,
        strategy: AIStrategy,
        stat_bonuses: dict[str, float] | None = None,
    ) -> None:
        """
        Swap AI strategy and optionally buff stats.
        Typical use: call when HP crosses a threshold.

            enemy.trigger_phase_transition(
                EnragedBossAI(),
                stat_bonuses={"move_speed": 80, "attack_power": 0.5},
            )
        """
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