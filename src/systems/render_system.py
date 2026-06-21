"""
systems/render_system.py
========================
Two-pass renderer: world space (Y-sorted) then screen-space UI.
Supports render interpolation via prev_position + alpha.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from core.game_object import Scene
from core.primitives import Vec2, Rect2


@dataclass
class Camera:
    position: Vec2 = field(default_factory=Vec2)
    bounds: Rect2 = field(default_factory=Rect2)
    zoom: float = 1.0
    trauma: float = 0.0                        # 0–1; shake = trauma²
    _shake_offset: Vec2 = field(default_factory=Vec2)

    def apply_shake(self, dt: float, decay: float = 1.2) -> None:
        self.trauma = max(0.0, self.trauma - decay * dt)
        intensity = self.trauma ** 2
        import random
        max_off = 8.0
        self._shake_offset = Vec2(
            random.uniform(-max_off, max_off) * intensity,
            random.uniform(-max_off, max_off) * intensity,
        )

    def world_to_screen(self, world_pos: Vec2, sw: int, sh: int) -> Vec2:
        sx = (world_pos.x - self.position.x) * self.zoom + sw / 2 + self._shake_offset.x
        sy = (world_pos.y - self.position.y) * self.zoom + sh / 2 + self._shake_offset.y
        return Vec2(sx, sy)

    def clamp_to_bounds(self) -> None:
        self.position.x = max(self.bounds.x, min(self.position.x, self.bounds.x + self.bounds.width))
        self.position.y = max(self.bounds.y, min(self.position.y, self.bounds.y + self.bounds.height))


@dataclass
class DrawCall:
    """All data needed to blit one sprite. Collected, sorted, then flushed."""
    z_index: int
    sort_y: float
    atlas: str
    src_rect: Rect2
    dst_pos: Vec2
    flip_x: bool = False
    color_mod: tuple[int, int, int, int] = (255, 255, 255, 255)
    alpha: float = 1.0

    def sort_key(self) -> tuple[int, float]:
        return (self.z_index, self.sort_y)


class AssetCache:
    """
    Lazy-loading texture cache. Pre-load atlases at level start
    via load_atlas() so _submit() never touches the file system.
    """

    def __init__(self) -> None:
        self._textures: dict[str, object] = {}

    def load_atlas(self, path: str, backend_load_fn) -> None:
        """backend_load_fn: e.g. pygame.image.load"""
        if path not in self._textures:
            self._textures[path] = backend_load_fn(path)

    def get(self, path: str) -> object:
        tex = self._textures.get(path)
        if tex is None:
            raise KeyError(f"Atlas not pre-loaded: {path!r}")
        return tex

    def unload(self, path: str) -> None:
        self._textures.pop(path, None)


class RenderSystem:
    """
    Two-pass renderer.

    Pass 1 — world space (camera offset applied):
        Sub-pass A: ShadowComponents  (z=0, always below sprites)
        Sub-pass B: SpriteComponents  (Y-sorted within z_index)
        Sub-pass C: World-space UI    (EnemyHealthBar — z=5)

    Pass 2 — screen space (no camera offset):
        HUD, ComboWidget, DamageNumber (z=10+)

    Z layers:
        Z_SHADOW     = 0
        Z_WORLD      = 1
        Z_PROJECTILE = 2
        Z_VFX        = 3
        Z_WORLD_UI   = 5
        Z_SCREEN_UI  = 10
    """

    Z_SHADOW     = 0
    Z_WORLD      = 1
    Z_PROJECTILE = 2
    Z_VFX        = 3
    Z_WORLD_UI   = 5
    Z_SCREEN_UI  = 10

    def __init__(self, screen_w: int, screen_h: int, asset_cache: AssetCache) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.assets = asset_cache
        self._draw_calls: list[DrawCall] = []

    def draw(self, scene: Scene, camera: Camera, alpha: float) -> None:
        """
        Main entry point. alpha = accumulator / FIXED_DT for interpolation.
        Call once per render frame (variable rate).
        """
        self._draw_calls.clear()

        self._collect_shadows(scene, camera, alpha)
        self._collect_sprites(scene, camera, alpha)
        self._collect_world_ui(scene, camera, alpha)

        # Y-sort: z_index primary, world-space Y secondary
        self._draw_calls.sort(key=lambda d: d.sort_key())

        for call in self._draw_calls:
            self._submit(call)

        self._draw_screen_ui(scene)

    def _interpolated_pos(self, obj, alpha: float) -> Vec2:
        prev = getattr(obj, "prev_position", obj.position)
        cur  = obj.position
        return Vec2(
            prev.x + (cur.x - prev.x) * alpha,
            prev.y + (cur.y - prev.y) * alpha,
        )

    def _get_src_rect(self, sprite, anim) -> Rect2:
        fw, fh = sprite.frame_width, sprite.frame_height
        col = anim.current_frame if anim else 0
        row = anim._current.sheet_row if (anim and anim._current) else 0
        return Rect2(col * fw, row * fh, fw, fh)

    def _collect_sprites(self, scene: Scene, camera: Camera, alpha: float) -> None:
        from components.sprite_component import SpriteComponent
        from core.components import AnimationComponent

        for obj in scene.find_by_tag("renderable"):
            sprite = obj.get_component(SpriteComponent)
            if sprite is None or not obj.visible:
                continue
            anim = obj.get_component(AnimationComponent)
            draw_pos   = self._interpolated_pos(obj, alpha)
            screen_pos = camera.world_to_screen(draw_pos, self.screen_w, self.screen_h)
            screen_pos.x += sprite.draw_offset.x
            screen_pos.y += sprite.draw_offset.y
            src = self._get_src_rect(sprite, anim)
            self._draw_calls.append(DrawCall(
                z_index   = obj.transform.z_index or self.Z_WORLD,
                sort_y    = draw_pos.y,
                atlas     = sprite.atlas,
                src_rect  = src,
                dst_pos   = screen_pos,
                flip_x    = not (anim.facing_right if anim else True),
                color_mod = sprite.color_mod,
                alpha     = sprite.alpha,
            ))

    def _collect_shadows(self, scene: Scene, camera: Camera, alpha: float) -> None:
        from components.shadow_component import ShadowComponent

        for obj in scene.find_by_tag("renderable"):
            shadow = obj.get_component(ShadowComponent)
            if shadow is None or not obj.visible:
                continue
            draw_pos   = self._interpolated_pos(obj, alpha)
            w, h, a    = shadow.get_draw_params()
            screen_pos = camera.world_to_screen(
                Vec2(draw_pos.x, shadow.ground_y), self.screen_w, self.screen_h
            )
            self._draw_calls.append(DrawCall(
                z_index  = self.Z_SHADOW,
                sort_y   = shadow.ground_y,
                atlas    = "__shadow__",
                src_rect = Rect2(0, 0, w, h),
                dst_pos  = screen_pos,
                alpha    = a,
            ))

    def _collect_world_ui(self, scene: Scene, camera: Camera, alpha: float) -> None:
        for bar in scene.find_by_tag("enemy_health_bar"):
            if hasattr(bar, "collect_draw_calls"):
                bar.collect_draw_calls(self._draw_calls, camera, self.screen_w, self.screen_h)

    def _draw_screen_ui(self, scene: Scene) -> None:
        for ui_elem in scene.find_by_tag("screen_ui"):
            if hasattr(ui_elem, "draw"):
                ui_elem.draw(self.screen_w, self.screen_h)

    def _submit(self, call: DrawCall) -> None:
        """
        Hand off to the graphics backend (pygame, pyglet, raylib …).
        Swap the body of this method to change backends.

        pygame example:
            if call.atlas == "__shadow__":
                pygame.draw.ellipse(screen, (0,0,0,80),
                    (call.dst_pos.x - call.src_rect.width/2,
                     call.dst_pos.y - call.src_rect.height/2,
                     call.src_rect.width, call.src_rect.height))
            else:
                tex = self.assets.get(call.atlas)
                tex.set_alpha(int(call.alpha * 255))
                screen.blit(tex,
                    (round(call.dst_pos.x), round(call.dst_pos.y)),
                    area=(call.src_rect.x, call.src_rect.y,
                          call.src_rect.width, call.src_rect.height))
        """
        pass   # replace with backend-specific draw call
