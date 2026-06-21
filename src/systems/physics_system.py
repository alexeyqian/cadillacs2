"""
systems/physics_system.py
==========================
Integrates velocity, applies gravity, resolves platform collisions.
Snapshots prev_position before integration for render interpolation.
"""

from __future__ import annotations

from core.game_object import Scene
from core.components import PhysicsComponent
from core.primitives import Vec2


class PhysicsSystem:
    """
    Fixed-timestep physics. Called at exactly 60 Hz by GameLoop.

    Resolution order:
        1. Snapshot prev_position (render interpolation).
        2. Integrate velocity → position (PhysicsComponent.update).
        3. Resolve overlaps against Platform colliders (AABB sweep).
        4. Update is_grounded; fire on_landed / on_fell callbacks.
    """

    def update(self, dt: float, scene: Scene) -> None:
        platforms = scene.find_by_tag("platform")

        for obj in scene.all_objects():
            phys = obj.get_component(PhysicsComponent)
            if phys is None or not obj.active:
                continue

            # Snapshot for render interpolation
            obj.prev_position = Vec2(obj.position.x, obj.position.y)

            # Integrate (PhysicsComponent handles gravity + friction)
            phys.update(dt)

            # Platform resolution
            was_grounded = phys.is_grounded
            phys.is_grounded = False

            for platform in platforms:
                from objects.platform import Platform
                if not isinstance(platform, Platform):
                    continue
                self._resolve_platform(obj, phys, platform, was_grounded)

            # on_landed / on_fell callbacks
            if phys.is_grounded and not was_grounded and phys.on_landed:
                phys.on_landed()
            elif not phys.is_grounded and was_grounded and phys.on_fell:
                phys.on_fell()

    def _resolve_platform(self, obj, phys: PhysicsComponent, platform, was_grounded: bool) -> None:
        """Simple AABB platform resolution."""
        from objects.platform import Platform
        p: Platform = platform

        # Approximate entity feet rect
        feet_y = obj.position.y
        feet_x = obj.position.x
        half_w = 16.0

        in_x = p.rect.x - half_w < feet_x < p.rect.x + p.rect.width + half_w
        crossing = (obj.prev_position.y <= p.rect.y < feet_y)

        if p.one_way:
            # One-way: only block when falling through from above
            if phys.velocity.y >= 0 and crossing and in_x:
                obj.position.y = p.rect.y
                phys.velocity.y = 0.0
                phys.is_grounded = True
        else:
            # Solid: full AABB resolution
            from core.primitives import Rect2
            entity_rect = Rect2(feet_x - half_w, feet_y - 64, half_w * 2, 64)
            if entity_rect.overlaps(p.rect):
                # Push up (standing on top)
                if phys.velocity.y >= 0 and crossing and in_x:
                    obj.position.y = p.rect.y
                    phys.velocity.y = 0.0
                    phys.is_grounded = True
