"""
core/game_object.py
===================
GameObject — root entity. Scene — scene container.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Type, TypeVar

from .component_base import ComponentBase
from .primitives import EventBus, Vec2

if TYPE_CHECKING:
    pass

T = TypeVar("T", bound=ComponentBase)


@dataclass
class Transform2D:
    position: Vec2 = field(default_factory=Vec2)
    rotation: float = 0.0
    scale: Vec2 = field(default_factory=lambda: Vec2(1.0, 1.0))
    z_index: int = 0


class Scene:
    """Owns all live GameObjects and the shared EventBus."""

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self._objects: dict[str, "GameObject"] = {}
        self._pending_spawn: list["GameObject"] = []
        self._pending_destroy: list["GameObject"] = []

    def spawn(self, obj: "GameObject") -> None:
        self._pending_spawn.append(obj)

    def destroy(self, obj: "GameObject") -> None:
        self._pending_destroy.append(obj)

    def find_by_id(self, entity_id: str) -> "GameObject | None":
        return self._objects.get(entity_id)

    def find_by_tag(self, tag: str) -> list["GameObject"]:
        return [o for o in self._objects.values() if o.has_tag(tag)]

    def all_objects(self) -> list["GameObject"]:
        return list(self._objects.values())

    def update(self, dt: float) -> None:
        for obj in self._pending_spawn:
            self._objects[obj.id] = obj
            obj.on_spawn(self)
        self._pending_spawn.clear()

        for obj in list(self._objects.values()):
            if obj.active:
                obj.update(dt)

        for obj in self._pending_destroy:
            obj.on_destroy()
            self._objects.pop(obj.id, None)
        self._pending_destroy.clear()


class GameObject:
    """
    Root entity class. All behaviour comes from attached ComponentBase subclasses.
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
        self._components: dict[type, list[ComponentBase]] = {}

        # Previous physics position for render interpolation
        self.prev_position: Vec2 = Vec2()

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

    @property
    def transform(self) -> Transform2D:
        return self._transform

    @property
    def position(self) -> Vec2:
        return self._transform.position

    @position.setter
    def position(self, value: Vec2) -> None:
        self._transform.position = value

    def add_component(self, component: ComponentBase) -> "GameObject":
        component.owner = self  # type: ignore[attr-defined]
        key = type(component)
        self._components.setdefault(key, []).append(component)
        component.on_start()
        return self

    def get_component(self, component_type: Type[T]) -> T | None:
        exact = self._components.get(component_type)
        if exact:
            return exact[0]  # type: ignore[return-value]
        for key, comps in self._components.items():
            if comps and issubclass(key, component_type):
                return comps[0]  # type: ignore[return-value]
        return None

    def require_component(self, component_type: Type[T]) -> T:
        c = self.get_component(component_type)
        if c is None:
            raise RuntimeError(f"[{self._name}] Missing component: {component_type.__name__}")
        return c

    def get_components(self, component_type: Type[T]) -> list[T]:
        return list(self._components.get(component_type, []))  # type: ignore[return-value]

    def remove_component(self, component_type: Type[T]) -> bool:
        removed = self._components.pop(component_type, [])
        for c in removed:
            c.on_destroy()
        return bool(removed)

    def has_component(self, component_type: Type[T]) -> bool:
        return bool(self._components.get(component_type))

    def on_spawn(self, scene: Scene) -> None:
        self._scene = scene

    def on_destroy(self) -> None:
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
