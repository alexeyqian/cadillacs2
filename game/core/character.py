"""
character.py
============
Character — combat-capable GameObject.

No ICharacter interface. Character is used directly as the base type
for Player and Enemy. Typed property accessors replace the interface contract.

CombatComponent is a plain class (not ComponentBase) because:
  - It has no need for the scene lifecycle hooks.
  - It is updated manually in Character.update() after components tick.
  - This keeps it easily unit-testable without a full scene.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .game_object import GameObject
from .primitives import Vec2
from .components import (
    AnimationComponent,
    CharacterStats,
    CollisionComponent,
    DamageInfo,
    HealthComponent,
    PhysicsComponent,
    StateMachineComponent,
    StatsComponent,
)

if TYPE_CHECKING:
    from .game_object import Scene


# ─────────────────────────────────────────────
# CombatComponent
# Frame-accurate attack FSM + combo tracking.
# Plain class — not a ComponentBase subclass.
# ─────────────────────────────────────────────

@dataclass
class AttackDef:
    """Data definition for one attack move. Authored in frame counts."""
    id: str
    startup_frames: int         # frames before hitbox activates
    active_frames: int          # frames the hitbox persists
    recovery_frames: int        # frames before another action is possible
    base_damage: float          # multiplied by stats.attack_power at hit time
    knockback: Vec2
    animation: str | None = None
    can_combo: bool = True      # can chain from another active attack


_FIXED_FPS: float = 60.0       # physics tick rate; frame counts divide by this


class CombatComponent:
    """
    Manages attack execution, hit-phase FSM, and combo tracking.

    Frame counts are the authoring unit (designer-friendly, genre convention).
    Internally converts to seconds for the dt-based update loop.

    Phase cycle: idle → startup → active → recovery → idle
    """

    def __init__(self) -> None:
        self.owner: "Character | None" = None

        self._attacks: dict[str, AttackDef] = {}
        self._combo_count: int = 0
        self._combo_timer: float = 0.0
        self.combo_window: float = 0.5          # seconds combo stays open after a hit

        self._current_atk: AttackDef | None = None
        self._atk_timer: float = 0.0
        self._atk_phase: str = "idle"           # startup | active | recovery | idle

        self.on_hit_landed: Callable[["AttackDef", "Character"], None] | None = None
        self.on_combo_break: Callable[[int], None] | None = None

    @property
    def is_attacking(self) -> bool:
        return self._atk_phase != "idle"

    @property
    def combo_count(self) -> int:
        return self._combo_count

    @property
    def current_attack(self) -> AttackDef | None:
        return self._current_atk

    def register_attack(self, definition: AttackDef) -> "CombatComponent":
        self._attacks[definition.id] = definition
        return self

    def start_attack(self, attack_id: str) -> bool:
        """
        Attempt to start an attack.
        Returns False if already in a phase that cannot be interrupted.
        """
        definition = self._attacks.get(attack_id)
        if definition is None:
            return False
        currently_cancellable = self._atk_phase == "active" and definition.can_combo
        if self.is_attacking and not currently_cancellable:
            return False
        self._current_atk = definition
        self._atk_phase = "startup"
        self._atk_timer = definition.startup_frames / _FIXED_FPS
        return True

    def update(self, dt: float) -> None:
        # Combo window decay
        if self._combo_timer > 0:
            self._combo_timer -= dt
            if self._combo_timer <= 0:
                if self.on_combo_break:
                    self.on_combo_break(self._combo_count)
                self._combo_count = 0

        if self._current_atk is None or self._atk_phase == "idle":
            return

        self._atk_timer -= dt
        if self._atk_timer > 0:
            return

        if self._atk_phase == "startup":
            self._atk_phase = "active"
            self._atk_timer = self._current_atk.active_frames / _FIXED_FPS
        elif self._atk_phase == "active":
            self._atk_phase = "recovery"
            self._atk_timer = self._current_atk.recovery_frames / _FIXED_FPS
        elif self._atk_phase == "recovery":
            self._atk_phase = "idle"
            self._current_atk = None

    def register_hit(self, target: "Character") -> None:
        """Called by the collision system when an active hitbox lands."""
        if self._current_atk is None or self._atk_phase != "active":
            return
        self._combo_count += 1
        self._combo_timer = self.combo_window
        if self.on_hit_landed:
            self.on_hit_landed(self._current_atk, target)


# ─────────────────────────────────────────────
# Character
# ─────────────────────────────────────────────

class Character(GameObject):
    """
    Combat-capable entity. Base class for Player and Enemy.

    Wires six shared components plus CombatComponent at construction.
    Typed property accessors give subclasses clean access without
    calling require_component() everywhere.

    Subclasses override update() to drive input (Player) or AI (Enemy),
    then call super().update(dt) to tick components.
    """

    def __init__(
        self,
        entity_id: str,
        name: str,
        base_stats: CharacterStats,
        max_health: int,
    ) -> None:
        super().__init__(entity_id, name)

        # Build via composition
        self._health        = HealthComponent(max_health)
        self._physics       = PhysicsComponent()
        self._collision     = CollisionComponent()
        self._state_machine = StateMachineComponent()
        self._animation     = AnimationComponent()
        self._stats         = StatsComponent(base_stats)
        self._combat        = CombatComponent()
        self._combat.owner  = self

        # Register ComponentBase subclasses with the engine
        (self
         .add_component(self._health)
         .add_component(self._physics)
         .add_component(self._collision)
         .add_component(self._state_machine)
         .add_component(self._animation)
         .add_component(self._stats))

    # ── Typed accessors ───────────────────────

    @property
    def health(self) -> HealthComponent:
        return self._health

    @property
    def physics(self) -> PhysicsComponent:
        return self._physics

    @property
    def collision(self) -> CollisionComponent:
        return self._collision

    @property
    def state_machine(self) -> StateMachineComponent:
        return self._state_machine

    @property
    def animation(self) -> AnimationComponent:
        return self._animation

    @property
    def stats(self) -> StatsComponent:
        return self._stats

    @property
    def combat(self) -> CombatComponent:
        return self._combat

    # ── Derived queries ───────────────────────

    @property
    def is_alive(self) -> bool:
        return self._health.is_alive

    @property
    def is_grounded(self) -> bool:
        return self._physics.is_grounded

    @property
    def facing_right(self) -> bool:
        return self._animation.facing_right

    # ── Actions ───────────────────────────────

    def move(self, direction: Vec2) -> None:
        """Apply directional movement scaled by move_speed. Horizontal axis only."""
        if not self.is_alive or self._combat.is_attacking:
            return
        speed = self._stats.get("move_speed")
        self._physics.velocity.x = direction.x * speed
        if direction.x != 0:
            self._animation.set_facing(direction.x > 0)

    def jump(self) -> None:
        if not self.is_alive or not self.is_grounded:
            return
        self._physics.velocity.y = -self._stats.get("jump_force")
        self._physics.is_grounded = False

    def attack(self, attack_id: str) -> bool:
        return self._combat.start_attack(attack_id)

    def take_damage(self, info: DamageInfo) -> None:
        if not self.is_alive:
            return
        defense = self._stats.get("defense")
        scaled = DamageInfo(
            amount=info.amount * (1.0 - defense),
            damage_type=info.damage_type,
            source=info.source,
            knockback=info.knockback,
        )
        self._health.take_damage(scaled)
        kb = scaled.knockback
        if kb.x != 0 or kb.y != 0:
            self._physics.apply_knockback(kb)

    def die(self) -> None:
        self._state_machine.transition("dead")
        self._collision.deactivate_all_hitboxes()
        self._physics.immovable = True

    # ── Update ────────────────────────────────

    def update(self, dt: float) -> None:
        super().update(dt)          # ticks all ComponentBase children
        self._combat.update(dt)     # manual tick — not a ComponentBase

    # ── Scene lifecycle ───────────────────────

    def on_spawn(self, scene: "Scene") -> None:
        super().on_spawn(scene)
        self._health.on_death = lambda _info: self.die()