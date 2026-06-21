"""
objects/pickup.py
=================
Collectible item. Generic — effect is data-driven via ItemData.
"""

from __future__ import annotations

from core.game_object import GameObject, Scene
from core.primitives import Rect2, Vec2


class Pickup(GameObject):
    """
    Spawned by LevelManager (static placement) or Enemy._spawn_drops.
    PickupSystem checks trigger_zone() overlap each frame.
    """

    def __init__(self, entity_id: str, item_data, position: Vec2) -> None:
        super().__init__(entity_id, f"Pickup_{item_data.id}")
        self.item_data = item_data
        self.position = position
        self.add_tag("pickup")
        self.add_tag("renderable")
        self._bob_elapsed: float = 0.0

    def trigger_zone(self) -> Rect2:
        """Overlap rect used by PickupSystem."""
        return Rect2(self.position.x - 16, self.position.y - 16, 32, 32)

    def update(self, dt: float) -> None:
        # Gentle bob animation
        self._bob_elapsed += dt
        import math
        self.position.y += math.sin(self._bob_elapsed * 3.0) * 0.5
