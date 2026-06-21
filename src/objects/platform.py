"""
objects/platform.py
====================
Static geometry. Minimal entity — no update loop.
PhysicsSystem reads platforms via scene.find_by_tag('platform').
"""

from __future__ import annotations

from core.game_object import GameObject
from core.primitives import Rect2, Vec2


class Platform(GameObject):
    """
    one_way=True  → character can jump through from below.
    one_way=False → solid from all sides.
    """

    def __init__(self, entity_id: str, rect: Rect2, one_way: bool = False) -> None:
        super().__init__(entity_id, "Platform")
        self.rect = rect
        self.one_way = one_way
        self.position = Vec2(rect.x, rect.y)
        self.add_tag("platform")

    def update(self, dt: float) -> None:
        pass   # static
