"""
core/component_base.py
======================
Single base class for all components. No separate interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_object import GameObject


class ComponentBase(ABC):
    """
    Base class for all components.

    Lifecycle:
        1. add_component(c) sets c.owner, calls c.on_start()
        2. Every frame: c.update(dt)  — skipped when c.enabled is False
        3. on_destroy() called when component or owner is removed
    """

    owner: "GameObject"
    enabled: bool = True

    def on_start(self) -> None:
        """Called once after attachment and owner is ready."""

    def on_destroy(self) -> None:
        """Called when the component or its owner is destroyed."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Called every frame. dt is delta-time in seconds."""
