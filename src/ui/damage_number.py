"""
ui/damage_number.py
====================
Pooled floating damage text. Spawned by VFXSystem on damage:taken.
Floats upward ~40px and fades out over lifetime seconds.
"""

from __future__ import annotations

from core.game_object import GameObject
from core.primitives import Vec2


class DamageNumber(GameObject):
    """
    Colour coding:
        White  → normal hit
        Yellow → high damage (> 20)
        Red    → player takes damage
        Green  → healing
    """

    def __init__(self, entity_id: str) -> None:
        super().__init__(entity_id, "DamageNumber")
        self.pool: object = None
        self._amount: int = 0
        self._color: tuple[int, int, int] = (255, 255, 255)
        self._elapsed: float = 0.0
        self.lifetime: float = 0.8
        self.rise_speed: float = 50.0
        self.active = False

    def setup(self, amount: int, position: Vec2, is_player_damage: bool = False, is_heal: bool = False) -> None:
        self._amount  = amount
        self._elapsed = 0.0
        self.position = Vec2(position.x, position.y)
        self.active   = True
        self.visible  = True

        if is_heal:
            self._color = (80, 220, 80)
        elif is_player_damage:
            self._color = (220, 60, 60)
        elif amount > 20:
            self._color = (255, 200, 50)
        else:
            self._color = (255, 255, 255)

    def reset(self) -> None:
        self.active  = False
        self.visible = False

    def update(self, dt: float) -> None:
        if not self.active:
            return
        self._elapsed += dt
        self.position.y -= self.rise_speed * dt
        if self._elapsed >= self.lifetime:
            if self.pool:
                getattr(self.pool, "release", lambda x: None)(self)
            elif self.scene:
                self.scene.destroy(self)

    def draw_alpha(self) -> float:
        """Fade out in the last 30% of lifetime."""
        fade_start = self.lifetime * 0.7
        if self._elapsed < fade_start:
            return 1.0
        return max(0.0, 1.0 - (self._elapsed - fade_start) / (self.lifetime - fade_start))
