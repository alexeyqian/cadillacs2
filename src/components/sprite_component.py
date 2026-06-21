"""
components/sprite_component.py
==============================
Holds texture reference and draw metadata.
AnimationComponent drives which frame; SpriteComponent stores the atlas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from core.component_base import ComponentBase
from core.primitives import Vec2


class SpriteComponent(ComponentBase):
    """
    Draw metadata for a sprite-sheet entity.

    frame_width / frame_height define one frame's size in the atlas.
    AnimationComponent.current_frame and sheet_row pick the source rect.
    draw_offset shifts the sprite relative to the entity pivot (position).
    color_mod is RGBA tint — (255,255,255,255) = unmodified.
    """

    def __init__(
        self,
        atlas: str,
        frame_width: int,
        frame_height: int,
        draw_offset: Vec2 | None = None,
    ) -> None:
        self.atlas = atlas
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.draw_offset: Vec2 = draw_offset or Vec2()
        self.color_mod: tuple[int, int, int, int] = (255, 255, 255, 255)
        self.alpha: float = 1.0

    def update(self, dt: float) -> None:
        pass
