"""
game_object.py
==============
GameObject — root of the entity hierarchy.

Mirrors:
  Godot  — Node2D
  Unity  — GameObject
  Unreal — AActor
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Type, TypeVar

from .component_base import ComponentBase
from .primitives import Vec2

if TYPE_CHECKING:
    from .primitives import EventBus


T = TypeVar("T", bound=ComponentBase)


# ─────────────────────────────────────────────
# Transform — plain data, no behaviour
# ─────────────────────────────────────────────

@dataclass
class Transform2D:
    position: Vec2 = field(default_factory=Vec2)
    rotation: float = 0.0                          # radians, clockwise in screen space
    scale: Vec2 = field(default_factory=lambda: Vec2(1.0, 1.0))
    z_index: int = 0


# ─────────────────────────────────────────────
# Scene — owns the object registry and event bus.
# Defined here to avoid a separate file for a small class;
# move to scene.py if it grows.
# ─────────────────────────────────────────────

class Scene:
    """
    Lightweight scene container.
    Holds all live GameObjects and the shared EventBus.
    The game loop calls scene.update(dt) each frame.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._objects: dict[str, GameObject] = {}
        self._pending_spawn: list[GameObject] = []
        self._pending_destroy: list[GameObject] = []

    def spawn(self, obj: GameObject) -> None:
        """Register an object and call on_spawn at end of frame."""
        self._pending_spawn.append(obj)

    def destroy(self, obj: GameObject) -> None:
        """Schedule object for removal at end of frame."""
        self._pending_destroy.append(obj)

    def find_by_id(self, entity_id: str) -> GameObject | None:
        return self._objects.get(entity_id)

    def find_by_tag(self, tag: str) -> list[GameObject]:
        return [o for o in self._objects.values() if o.has_tag(tag)]

    def update(self, dt: float) -> None:
        # Flush spawns first
        for obj in self._pending_spawn:
            self._objects[obj.id] = obj
            obj.on_spawn(self)
        self._pending_spawn.clear()

        # Tick live objects
        for obj in list(self._objects.values()):
            if obj.active:
                obj.update(dt)

        # Flush destroys
        for obj in self._pending_destroy:
            obj.on_destroy()
            self._objects.pop(obj.id, None)
        self._pending_destroy.clear()


# ─────────────────────────────────────────────
# GameObject
# ─────────────────────────────────────────────

class GameObject:
    """
    Root entity class. Subclass to add domain-specific typed accessors
    (Character, Pickup, Projectile …).

    All reusable behaviour is delivered via ComponentBase subclasses
    attached with add_component() — composition over inheritance.
    """

    def __init__(self, entity_id: str, name: str = "GameObject") -> None:
        self._id = entity_id
        self._name = name
        self._tags: set[str] = set()
        self._transform = Transform2D()
        self._active = True
        self._visible = True
        self._destroyed = False
        self._scene: Scene | None = None

        # Registry: concrete type → ordered list of components.
        # List supports multiple components of the same type (rare but valid).
        self._components: dict[type, list[ComponentBase]] = {}

    # ── Identity ──────────────────────────────

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def tags(self) -> frozenset[str]:
        return frozenset(self._tags)

    def add_tag(self, tag: str) -> None:
        self._tags.add(tag)

    def remove_tag(self, tag: str) -> None:
        self._tags.discard(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self._tags

    # ── Transform ─────────────────────────────

    @property
    def transform(self) -> Transform2D:
        return self._transform

    @property
    def position(self) -> Vec2:
        return self._transform.position

    @position.setter
    def position(self, value: Vec2) -> None:
        self._transform.position = value

    # ── Component system ──────────────────────

    def add_component(self, component: ComponentBase) -> "GameObject":
        """
        Attach a component. Wires owner, then calls on_start().
        Returns self for fluent chaining:
            go.add_component(HealthComponent(100)).add_component(PhysicsComponent())
        """
        component.owner = self
        key = type(component)
        self._components.setdefault(key, []).append(component)
        component.on_start()
        return self

    def get_component(self, component_type: Type[T]) -> T | None:
        """
        Return the first attached component of the given type.
        Also matches subclasses, so get_component(ComponentBase) finds anything.
        Returns None if not found — caller decides if that is an error.
        """
        # Fast path: exact type match
        exact = self._components.get(component_type)
        if exact:
            return exact[0]  # type: ignore[return-value]
        # Slow path: subclass match (used sparingly)
        for key, comps in self._components.items():
            if comps and issubclass(key, component_type):
                return comps[0]  # type: ignore[return-value]
        return None

    def require_component(self, component_type: Type[T]) -> T:
        """Like get_component but raises RuntimeError if not found."""
        component = self.get_component(component_type)
        if component is None:
            raise RuntimeError(
                f"[{self._name}] Missing required component: {component_type.__name__}"
            )
        return component

    def get_components(self, component_type: Type[T]) -> list[T]:
        """Return all attached components of the given type."""
        return list(self._components.get(component_type, []))  # type: ignore[return-value]

    def remove_component(self, component_type: Type[T]) -> bool:
        """Detach and destroy all components of the given type."""
        removed = self._components.pop(component_type, [])
        for c in removed:
            c.on_destroy()
        return bool(removed)

    def has_component(self, component_type: Type[T]) -> bool:
        return bool(self._components.get(component_type))

    # ── Lifecycle ─────────────────────────────

    def on_spawn(self, scene: Scene) -> None:
        """Called by Scene after the object is registered."""
        self._scene = scene

    def on_destroy(self) -> None:
        """Called by Scene before the object is removed."""
        if self._destroyed:
            return
        self._destroyed = True
        for components in reversed(list(self._components.values())):
            for c in reversed(components):
                c.on_destroy()
        self._components.clear()

    def update(self, dt: float) -> None:
        if not self._active or self._destroyed:
            return
        for components in self._components.values():
            for c in components:
                if c.enabled:
                    c.update(dt)

    # ── State ─────────────────────────────────

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        self._active = value

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

    @property
    def destroyed(self) -> bool:
        return self._destroyed

    @property
    def scene(self) -> Scene | None:
        return self._scene

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self._id!r}, name={self._name!r})"