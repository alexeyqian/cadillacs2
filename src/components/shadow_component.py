"""
components/shadow_component.py
================================
Blob shadow drawn on the ground plane beneath the entity.
Scale and opacity decrease as the entity rises above ground_y.
Rendered by RenderSystem before sprites (always below).
"""

from __future__ import annotations

from core.component_base import ComponentBase


class ShadowComponent(ComponentBase):

    def __init__(
        self,
        base_width: float = 28.0,
        base_height: float = 8.0,
        ground_y: float = 0.0,
    ) -> None:
        self.base_width = base_width
        self.base_height = base_height
        self.ground_y = ground_y   # Y of the platform surface; set at spawn

    def update(self, dt: float) -> None:
        pass

    def get_draw_params(self) -> tuple[float, float, float]:
        """Returns (width, height, alpha) scaled by height above ground."""
        height_above = max(0.0, self.ground_y - self.owner.position.y)
        scale = max(0.3, 1.0 - height_above / 120.0)
        return self.base_width * scale, self.base_height * scale, scale
