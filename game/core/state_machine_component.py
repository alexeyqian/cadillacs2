from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .component_base import ComponentBase
from .primitives import Rect2, Vec2

if TYPE_CHECKING:
    from .game_object import GameObject

# ─────────────────────────────────────────────
# StateMachineComponent
# ─────────────────────────────────────────────

class State:
    """
    Base class for FSM states. Not abstract — override only what you need.
    Name must be set as a class attribute or in __init__.
    """

    name: str = "unnamed"

    def on_enter(self, prev: str | None) -> None:
        pass

    def on_exit(self, next_name: str) -> None:
        pass

    def update(self, dt: float) -> None:
        pass


class StateMachineComponent(ComponentBase):
    """
    Code-first finite-state machine.
    Emits 'state:changed' on the scene event bus so external systems
    (HUD, audio) can react without coupling to the character.
    """

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
                "object": self.owner,
                "from": prev_name or "",
                "to": name,
            })

    def update(self, dt: float) -> None:
        if self._current:
            self._current.update(dt)

