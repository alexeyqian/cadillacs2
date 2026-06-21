"""
ui/enemy_health_bar.py
=======================
World-space health bar drawn above each enemy.
Shown only while the enemy was recently hit; fades out after fade_duration.
"""

from __future__ import annotations

from core.game_object import GameObject
from core.primitives import Vec2, Rect2
from systems.render_system import DrawCall, Camera


class EnemyHealthBar(GameObject):
    """
    One per enemy. Tagged 'enemy_health_bar' so RenderSystem
    calls collect_draw_calls() in the world-UI sub-pass.
    """

    def __init__(self, entity_id: str, enemy, fade_duration: float = 2.0) -> None:
        super().__init__(entity_id, "EnemyHealthBar")
        self.enemy         = enemy
        self.fade_duration = fade_duration
        self._fade_timer   = 0.0
        self._visible_flag = False
        self.add_tag("enemy_health_bar")

    def on_spawn(self, scene) -> None:
        super().on_spawn(scene)
        if scene:
            scene.event_bus.on("damage:taken", self._on_damage)

    def _on_damage(self, payload) -> None:
        if payload.get("target") is self.enemy:
            self._fade_timer   = self.fade_duration
            self._visible_flag = True

    def update(self, dt: float) -> None:
        if self._fade_timer > 0:
            self._fade_timer -= dt
            if self._fade_timer <= 0:
                self._visible_flag = False

        # Follow the enemy
        if self.enemy and not self.enemy.destroyed:
            self.position = Vec2(self.enemy.position.x, self.enemy.position.y - 80)
        else:
            if self.scene:
                self.scene.destroy(self)

    def collect_draw_calls(
        self,
        draw_calls: list[DrawCall],
        camera: Camera,
        sw: int,
        sh: int,
    ) -> None:
        if not self._visible_flag or self.enemy is None or self.enemy.destroyed:
            return
        h     = self.enemy.health
        pct   = h.health_percent
        alpha = min(1.0, self._fade_timer / self.fade_duration)
        screen_pos = camera.world_to_screen(self.position, sw, sh)

        bar_w, bar_h = 60, 6
        # Background bar
        draw_calls.append(DrawCall(
            z_index=5, sort_y=self.position.y,
            atlas="__rect__",
            src_rect=Rect2(0, 0, bar_w, bar_h),
            dst_pos=Vec2(screen_pos.x - bar_w / 2, screen_pos.y),
            color_mod=(60, 20, 20, 255),
            alpha=alpha,
        ))
        # HP fill
        draw_calls.append(DrawCall(
            z_index=5, sort_y=self.position.y,
            atlas="__rect__",
            src_rect=Rect2(0, 0, int(bar_w * pct), bar_h),
            dst_pos=Vec2(screen_pos.x - bar_w / 2, screen_pos.y),
            color_mod=(220, 60, 60, 255),
            alpha=alpha,
        ))
