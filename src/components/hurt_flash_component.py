"""
components/hurt_flash_component.py
====================================
Flashes the sprite white/red for a fixed number of frames on hit.
Essential for game feel — without it hits feel soft regardless of audio.
"""

from __future__ import annotations

from core.component_base import ComponentBase
from core.components import DamageInfo


class HurtFlashComponent(ComponentBase):

    def __init__(self, flash_frames: int = 4) -> None:
        self.flash_frames = flash_frames
        self._remaining: int = 0

    def on_start(self) -> None:
        from core.components import HealthComponent
        health = self.owner.get_component(HealthComponent)
        if health:
            _prev = health.on_damage
            def _chained(info: DamageInfo, amount: int) -> None:
                self._remaining = self.flash_frames
                if _prev:
                    _prev(info, amount)
            health.on_damage = _chained

    def update(self, dt: float) -> None:
        if self._remaining <= 0:
            return
        self._remaining -= 1
        from components.sprite_component import SpriteComponent
        sprite = self.owner.get_component(SpriteComponent)
        if sprite:
            # Alternate between white flash and red tint each frame
            if self._remaining % 2 == 1:
                sprite.color_mod = (255, 255, 255, 255)
            else:
                sprite.color_mod = (255, 80, 80, 255)
            if self._remaining == 0:
                sprite.color_mod = (255, 255, 255, 255)
