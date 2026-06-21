"""
component_base.py
=================
ComponentBase — the single base class for all components.

Subclass this and override only the methods you need.
update() is the only abstract method — every component must tick.
on_start() and on_destroy() are no-ops by default.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_object import GameObject


class ComponentBase(ABC):
    """
    Base class for all components.

    Lifecycle (called by GameObject):
        1. add_component(c) sets c.owner, then calls c.on_start()
        2. Every frame: c.update(dt)  — skipped when c.enabled is False
        3. on_destroy() is called when the component or owner is removed

    The owner slot is written by GameObject.add_component() before on_start()
    is called, so it is safe to access self.owner inside on_start().
    """

    # Written by GameObject.add_component() — never None after attachment.
    owner: "GameObject"
    enabled: bool = True

    def on_start(self) -> None:
        """Called once after the component is attached and owner is ready."""

    def on_destroy(self) -> None:
        """Called when the component or its owner is destroyed."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Called every frame. dt is delta-time in seconds."""