# backends/pygame_renderer.py
from __future__ import annotations

import pygame
from systems.render_interface import IRenderer, TextureHandle
from core.primitives import Rect2, Vec2
from core.paths import SRC_DIR
from pathlib import Path


class PygameRenderer(IRenderer):
    """
    Pygame implementation of IRenderer.
    Import this only in main.py (or wherever you boot the game).
    """

    def __init__(self, width: int, height: int, title: str = "Beat-Em-Up") -> None:
        pygame.init()
        self._screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self._clock  = pygame.time.Clock()
        self._width  = width
        self._height = height

        # Internal map: handle.id → pygame.Surface
        # The engine never sees pygame.Surface — only TextureHandle.
        self._surfaces: dict[str, pygame.Surface] = {}

        # Font cache
        self._fonts: dict[int, pygame.font.Font] = {}

    # ── Lifecycle ─────────────────────────────────────────

    def begin_frame(self) -> None:
        pass   # pygame has no explicit begin-frame

    def end_frame(self) -> None:
        pygame.display.flip()

    def clear(self, color: tuple[int, int, int, int] = (0, 0, 0, 255)) -> None:
        self._screen.fill(color[:3])

    # ── Asset loading ─────────────────────────────────────

    def load_texture(self, path: str) -> TextureHandle:
        if path not in self._surfaces:
            full = Path(path) if Path(path).is_absolute() else SRC_DIR / path
            surface = pygame.image.load(str(full)).convert_alpha()
            self._surfaces[path] = surface
        surface = self._surfaces[path]
        return TextureHandle(id=path, width=surface.get_width(), height=surface.get_height())

    def unload_texture(self, handle: TextureHandle) -> None:
        self._surfaces.pop(handle.id, None)

    # ── Drawing ───────────────────────────────────────────

    def draw_texture(
        self,
        handle: TextureHandle,
        src: Rect2,
        dst: Vec2,
        flip_x: bool = False,
        color_mod: tuple[int, int, int, int] = (255, 255, 255, 255),
        alpha: float = 1.0,
    ) -> None:
        surface = self._surfaces.get(handle.id)
        if surface is None:
            return

        src_rect = pygame.Rect(src.x, src.y, src.width, src.height)
        sub = surface.subsurface(src_rect).copy()

        if flip_x:
            sub = pygame.transform.flip(sub, True, False)

        # Color modulation
        r, g, b, a = color_mod
        sub.fill((r, g, b, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Alpha
        sub.set_alpha(int(alpha * a))

        self._screen.blit(sub, (round(dst.x), round(dst.y)))

    def draw_rect(
        self,
        rect: Rect2,
        color: tuple[int, int, int, int],
        filled: bool = True,
    ) -> None:
        r, g, b, a = color
        # Use a surface for alpha support
        surf = pygame.Surface((int(rect.width), int(rect.height)), pygame.SRCALPHA)
        if filled:
            surf.fill((r, g, b, a))
        else:
            pygame.draw.rect(surf, (r, g, b, a),
                             (0, 0, int(rect.width), int(rect.height)), 1)
        self._screen.blit(surf, (round(rect.x), round(rect.y)))

    def draw_ellipse(
        self,
        center: Vec2,
        rx: float,
        ry: float,
        color: tuple[int, int, int, int],
    ) -> None:
        r, g, b, a = color
        w, h = int(rx * 2), int(ry * 2)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (r, g, b, a), (0, 0, w, h))
        self._screen.blit(surf, (round(center.x - rx), round(center.y - ry)))

    def draw_text(
        self,
        text: str,
        position: Vec2,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
        size: int = 16,
        align: str = "left",
    ) -> None:
        if size not in self._fonts:
            self._fonts[size] = pygame.font.SysFont("monospace", size)
        font = self._fonts[size]
        r, g, b, a = color
        surf = font.render(text, True, (r, g, b))
        surf.set_alpha(a)
        x = round(position.x)
        if align == "center":
            x -= surf.get_width() // 2
        elif align == "right":
            x -= surf.get_width()
        self._screen.blit(surf, (x, round(position.y)))

    # ── Queries ───────────────────────────────────────────

    @property
    def screen_width(self) -> int:
        return self._width

    @property
    def screen_height(self) -> int:
        return self._height