"""
core/character.py
=================
CombatComponent and Character base class.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .game_object import GameObject
from .primitives import Rect2, Vec2
from .components import (
    AnimationComponent, CharacterStats, CollisionComponent,
    DamageInfo, HealthComponent, HitboxDef, PhysicsComponent,
    StateMachineComponent, StatsComponent,
)

if TYPE_CHECKING:
    from .game_object import Scene

_FIXED_FPS: float = 60.0


@dataclass
class AttackDef:
    id: str
    startup_frames: int
    active_frames: int
    recovery_frames: int
    base_damage: float
    knockback: Vec2
    hitbox: Rect2 = field(default_factory=lambda: Rect2(30, -80, 60, 50))
    animation: str | None = None
    can_combo: bool = True


class CombatComponent:
    """
    Frame-accurate attack FSM + combo tracking.
    Plain class (not ComponentBase) — updated manually in Character.update().
    Phase cycle: idle → startup → active → recovery → idle.
    """

    def __init__(self) -> None:
        self.owner: "Character | None" = None
        self._attacks: dict[str, AttackDef] = {}
        self._combo_count: int = 0
        self._combo_timer: float = 0.0
        self.combo_window: float = 0.5
        self._current_atk: AttackDef | None = None
        self._atk_timer: float = 0.0
        self._atk_phase: str = "idle"
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

    @property
    def atk_phase(self) -> str:
        return self._atk_phase

    def register_attack(self, definition: AttackDef) -> "CombatComponent":
        self._attacks[definition.id] = definition
        return self

    def start_attack(self, attack_id: str) -> bool:
        definition = self._attacks.get(attack_id)
        if definition is None:
            return False
        if self.is_attacking and not (self._atk_phase == "active" and definition.can_combo):
            return False
        self._current_atk = definition
        self._atk_phase = "startup"
        self._atk_timer = definition.startup_frames / _FIXED_FPS
        # Upsert hitbox geometry into CollisionComponent so it's ready for activation
        if self.owner:
            col = self.owner.get_component(CollisionComponent)
            if col:
                col.hitboxes[definition.id] = HitboxDef(
                    id=definition.id,
                    rect=definition.hitbox,
                    damage=definition.base_damage,
                    knockback=definition.knockback,
                    active=False,
                )
        return True

    def update(self, dt: float) -> None:
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
            if self.owner:
                col = self.owner.get_component(CollisionComponent)
                if col:
                    col.activate_hitbox(self._current_atk.id)
        elif self._atk_phase == "active":
            self._atk_phase = "recovery"
            self._atk_timer = self._current_atk.recovery_frames / _FIXED_FPS
            if self.owner:
                col = self.owner.get_component(CollisionComponent)
                if col:
                    col.deactivate_all_hitboxes()
        elif self._atk_phase == "recovery":
            self._atk_phase = "idle"
            self._current_atk = None

    def register_hit(self, target: "Character") -> None:
        if self._current_atk is None or self._atk_phase != "active":
            return
        self._combo_count += 1
        self._combo_timer = self.combo_window
        if self.on_hit_landed:
            self.on_hit_landed(self._current_atk, target)


class Character(GameObject):
    """
    Combat-capable entity. Base for Player and Enemy.
    Wires six shared components + CombatComponent at construction.
    """

    def __init__(self, entity_id: str, name: str, base_stats: CharacterStats, max_health: int) -> None:
        super().__init__(entity_id, name)
        self._health        = HealthComponent(max_health)
        self._physics       = PhysicsComponent()
        self._collision     = CollisionComponent()
        self._state_machine = StateMachineComponent()
        self._animation     = AnimationComponent()
        self._stats         = StatsComponent(base_stats)
        self._combat        = CombatComponent()
        self._combat.owner  = self
        (self
         .add_component(self._health)
         .add_component(self._physics)
         .add_component(self._collision)
         .add_component(self._state_machine)
         .add_component(self._animation)
         .add_component(self._stats))
        self.add_tag("renderable")

    @property
    def health(self) -> HealthComponent:       return self._health
    @property
    def physics(self) -> PhysicsComponent:     return self._physics
    @property
    def collision(self) -> CollisionComponent: return self._collision
    @property
    def state_machine(self) -> StateMachineComponent: return self._state_machine
    @property
    def animation(self) -> AnimationComponent: return self._animation
    @property
    def stats(self) -> StatsComponent:         return self._stats
    @property
    def combat(self) -> CombatComponent:       return self._combat
    @property
    def is_alive(self) -> bool:                return self._health.is_alive
    @property
    def is_grounded(self) -> bool:             return self._physics.is_grounded
    @property
    def facing_right(self) -> bool:            return self._animation.facing_right

    def move(self, direction: Vec2) -> None:
        if not self.is_alive or self._combat.is_attacking:
            return
        speed = self._stats.get("move_speed")
        self._physics.velocity.x = direction.x * speed
        self._physics.velocity.y = direction.y * speed * 0.6  # depth movement
        if direction.x != 0:
            self._animation.set_facing(direction.x > 0)

    def jump(self) -> None:
        if not self.is_alive or not self.is_grounded:
            return
        self._physics.vz = self._stats.get("jump_force")

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

    def update(self, dt: float) -> None:
        super().update(dt)
        self._combat.update(dt)

    def on_spawn(self, scene: "Scene") -> None:
        super().on_spawn(scene)
        self._health.on_death = lambda _info: self.die()
