"""
core/components.py
==================
Shared reusable components: Health, Physics, Collision,
StateMachine, Animation, Stats.
"""

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
    amount: float
    damage_type: str = "physical"
    source: "GameObject | None" = None
    knockback: Vec2 = field(default_factory=Vec2)


class HealthComponent(ComponentBase):
    """
    HP, shield absorption, invincibility frames.
    HP is int. take_damage() returns int (math.floor — favours defender).
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
        if not self.is_alive or self.is_invincible:
            return 0
        dmg: float = info.amount
        if self.current_shield > 0:
            absorbed = min(float(self.current_shield), dmg)
            self.current_shield -= math.floor(absorbed)
            dmg -= absorbed
        hp_removed: int = min(math.floor(dmg), self.current_health)
        self.current_health -= hp_removed
        self._invincibility_timer = self.invincibility_duration
        if self.on_damage:
            self.on_damage(info, hp_removed)
        scene = self.owner.scene if hasattr(self, "owner") else None
        if scene:
            scene.event_bus.emit("damage:taken", {
                "target": self.owner, "amount": hp_removed, "source": info.source
            })
        if not self.is_alive:
            if self.on_death:
                self.on_death(info)
            if scene:
                scene.event_bus.emit("object:died", {
                    "object": self.owner, "killed_by": info.source
                })
        return hp_removed

    def heal(self, amount: int) -> int:
        actual = min(amount, self.max_health - self.current_health)
        self.current_health += actual
        if self.on_heal:
            self.on_heal(actual, self.current_health)
        return actual


# ─────────────────────────────────────────────
# PhysicsComponent
# ─────────────────────────────────────────────

class PhysicsComponent(ComponentBase):
    """Per-entity physics state. PhysicsSystem does resolution."""

    def __init__(self) -> None:
        self.velocity: Vec2 = Vec2()
        self.gravity: float = 980.0
        self.max_fall_speed: float = 1200.0
        self.is_grounded: bool = False
        self.friction: float = 0.18
        self.immovable: bool = False
        self.on_landed: Callable[[], None] | None = None
        self.on_fell: Callable[[], None] | None = None

    def update(self, dt: float) -> None:
        pass  # PhysicsSystem owns all integration; this component holds state only

    def apply_impulse(self, impulse: Vec2) -> None:
        self.velocity.x += impulse.x
        self.velocity.y += impulse.y

    def apply_knockback(self, knockback: Vec2) -> None:
        self.velocity.x = knockback.x
        self.velocity.y = knockback.y
        self.is_grounded = False


# ─────────────────────────────────────────────
# CollisionComponent
# ─────────────────────────────────────────────

@dataclass
class HitboxDef:
    id: str
    rect: Rect2
    damage: float
    knockback: Vec2
    active: bool = False


class CollisionComponent(ComponentBase):
    """Hurtbox (receives damage) and named attack hitboxes (deal damage)."""

    def __init__(self) -> None:
        self.hurtbox: Rect2 = Rect2(0, 0, 32, 64)
        self.hitboxes: dict[str, HitboxDef] = {}
        self.layer: int = 0
        self.mask: int = 0
        self.on_hit: Callable[[HitboxDef, "GameObject"], None] | None = None
        self.on_hurtbox_hit: Callable[[DamageInfo], None] | None = None

    def update(self, dt: float) -> None:
        pass

    def activate_hitbox(self, hitbox_id: str) -> None:
        if hitbox_id in self.hitboxes:
            self.hitboxes[hitbox_id].active = True

    def deactivate_hitbox(self, hitbox_id: str) -> None:
        if hitbox_id in self.hitboxes:
            self.hitboxes[hitbox_id].active = False

    def deactivate_all_hitboxes(self) -> None:
        for h in self.hitboxes.values():
            h.active = False

    def get_active_hitboxes(self) -> list[HitboxDef]:
        return [h for h in self.hitboxes.values() if h.active]

    def world_hurtbox(self) -> Rect2:
        """Hurtbox in world space."""
        pos = self.owner.position
        return Rect2(
            pos.x + self.hurtbox.x,
            pos.y + self.hurtbox.y,
            self.hurtbox.width,
            self.hurtbox.height,
        )

    def world_hitbox(self, h: HitboxDef) -> Rect2:
        """Single hitbox in world space, respecting facing direction."""
        pos = self.owner.position
        facing = 1.0
        from core.components import AnimationComponent
        anim = self.owner.get_component(AnimationComponent)
        if anim and not anim.facing_right:
            facing = -1.0
        return Rect2(
            pos.x + h.rect.x * facing,
            pos.y + h.rect.y,
            h.rect.width,
            h.rect.height,
        )


# ─────────────────────────────────────────────
# StateMachineComponent
# ─────────────────────────────────────────────

class State:
    """Base FSM state. Override only what you need."""
    name: str = "unnamed"

    def on_enter(self, prev: str | None) -> None:
        pass

    def on_exit(self, next_name: str) -> None:
        pass

    def update(self, dt: float) -> None:
        pass


class StateMachineComponent(ComponentBase):
    def __init__(self) -> None:
        self._states: dict[str, State] = {}
        self._current: State | None = None

    @property
    def current_state(self) -> str | None:
        return self._current.name if self._current else None

    def register_state(self, state: State) -> "StateMachineComponent":
        self._states[state.name] = state
        return self

    def transition(self, name: str) -> None:
        if self._current and self._current.name == name:
            return
        next_state = self._states.get(name)
        if next_state is None:
            raise KeyError(f"Unknown state: {name!r}")
        prev_name = self._current.name if self._current else None
        if self._current:
            self._current.on_exit(name)
        self._current = next_state
        next_state.on_enter(prev_name)
        scene = self.owner.scene if hasattr(self, "owner") else None
        if scene:
            scene.event_bus.emit("state:changed", {
                "object": self.owner, "from": prev_name or "", "to": name
            })

    def update(self, dt: float) -> None:
        if self._current:
            self._current.update(dt)


# ─────────────────────────────────────────────
# AnimationComponent
# ─────────────────────────────────────────────

@dataclass
class AnimationDef:
    name: str
    frame_count: int
    fps: float
    loop: bool
    sheet_row: int


class AnimationComponent(ComponentBase):
    def __init__(self) -> None:
        self._anims: dict[str, AnimationDef] = {}
        self._current: AnimationDef | None = None
        self._frame: int = 0
        self._elapsed: float = 0.0
        self._playing: bool = False
        self._facing_right: bool = True
        self.on_animation_finished: Callable[[str], None] | None = None

    @property
    def current_animation(self) -> str | None:
        return self._current.name if self._current else None

    @property
    def current_frame(self) -> int:
        return self._frame

    @property
    def facing_right(self) -> bool:
        return self._facing_right

    def register_animation(self, definition: AnimationDef) -> "AnimationComponent":
        self._anims[definition.name] = definition
        return self

    def play(self, name: str, force: bool = False) -> None:
        if not force and self._current and self._current.name == name:
            return
        anim = self._anims.get(name)
        if anim is None:
            return
        self._current = anim
        self._frame = 0
        self._elapsed = 0.0
        self._playing = True

    def set_facing(self, right: bool) -> None:
        self._facing_right = right

    def update(self, dt: float) -> None:
        if not self._playing or self._current is None:
            return
        self._elapsed += dt
        frame_dur = 1.0 / self._current.fps
        while self._elapsed >= frame_dur:
            self._elapsed -= frame_dur
            self._frame += 1
            if self._frame >= self._current.frame_count:
                if self._current.loop:
                    self._frame = 0
                else:
                    self._frame = self._current.frame_count - 1
                    self._playing = False
                    if self.on_animation_finished:
                        self.on_animation_finished(self._current.name)
                    break


# ─────────────────────────────────────────────
# StatsComponent
# ─────────────────────────────────────────────

@dataclass
class CharacterStats:
    move_speed: float = 220.0
    jump_force: float = 550.0
    attack_power: float = 1.0
    defense: float = 0.0
    recovery_frames: int = 8


class StatsComponent(ComponentBase):
    def __init__(self, base: CharacterStats) -> None:
        import copy
        self.base: CharacterStats = copy.copy(base)
        self.bonuses: dict[str, float] = {}

    def get(self, stat: str) -> float:
        return float(getattr(self.base, stat, 0.0)) + self.bonuses.get(stat, 0.0)

    def update(self, dt: float) -> None:
        pass
