# systems/renderer_interface.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from core.primitives import Rect2, Vec2


@dataclass
class TextureHandle:
    """
    Opaque reference to a loaded texture.
    The engine holds this; the backend knows what it actually is.
    Deliberately contains nothing backend-specific.
    """
    id: str        # the original path — used as cache key
    width: int
    height: int


class IRenderer(ABC):
    """
    Stable rendering contract. The engine calls these methods.
    Backends implement them. Nothing else is imported from any
    graphics library anywhere in the engine.

    All coordinates are in screen pixels (ints for pixel-perfect output).
    All colours are (r, g, b, a) tuples, values 0-255.
    """

    # ── Lifecycle ─────────────────────────────────────────

    @abstractmethod
    def begin_frame(self) -> None:
        """Called once at the start of each render frame."""

    @abstractmethod
    def end_frame(self) -> None:
        """Called once at the end — flips the display buffer."""

    @abstractmethod
    def clear(self, color: tuple[int, int, int, int] = (0, 0, 0, 255)) -> None:
        """Clear the framebuffer to a solid colour."""

    # ── Asset loading ─────────────────────────────────────

    @abstractmethod
    def load_texture(self, path: str) -> TextureHandle:
        """
        Load an image from disk and return an opaque handle.
        Called once per atlas at level-load time.
        Never called mid-frame.
        """

    @abstractmethod
    def unload_texture(self, handle: TextureHandle) -> None:
        """Release GPU/memory resources for this texture."""

    # ── Drawing ───────────────────────────────────────────

    @abstractmethod
    def draw_texture(
        self,
        handle: TextureHandle,
        src: Rect2,                          # source rect within the atlas
        dst: Vec2,                           # screen-space top-left (pixel-perfect)
        flip_x: bool = False,
        color_mod: tuple[int, int, int, int] = (255, 255, 255, 255),
        alpha: float = 1.0,
    ) -> None:
        """Blit a region of a texture to the screen."""

    @abstractmethod
    def draw_rect(
        self,
        rect: Rect2,
        color: tuple[int, int, int, int],
        filled: bool = True,
    ) -> None:
        """Draw a filled or outlined rectangle. Used for debug boxes and UI bars."""

    @abstractmethod
    def draw_ellipse(
        self,
        center: Vec2,
        rx: float,
        ry: float,
        color: tuple[int, int, int, int],
    ) -> None:
        """Draw a filled ellipse. Used for blob shadows."""

    @abstractmethod
    def draw_text(
        self,
        text: str,
        position: Vec2,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
        size: int = 16,
        align: str = "left",               # "left" | "center" | "right"
    ) -> None:
        """Draw a string. Used by HUD, DamageNumber, ComboWidget."""

    # ── Queries ───────────────────────────────────────────

    @property
    @abstractmethod
    def screen_width(self) -> int: ...

    @property
    @abstractmethod
    def screen_height(self) -> int: ...