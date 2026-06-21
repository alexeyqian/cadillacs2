from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from .component_base import ComponentBase
from .primitives import Rect2, Vec2

if TYPE_CHECKING:
    from .game_object import GameObject
# ─────────────────────────────────────────────
# AnimationComponent
# ─────────────────────────────────────────────

@dataclass
class AnimationDef:
    name: str
    frame_count: int
    fps: float
    loop: bool
    sheet_row: int          # sprite sheet row or atlas key


class AnimationComponent(ComponentBase):
    """
    Frame-accurate sprite animation driver.
    The renderer reads current_frame and facing_right each draw call.
    """

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

