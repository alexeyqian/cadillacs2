"""
systems/physics_system.py
==========================
Integrates velocity, applies gravity and friction, resolves platform collisions.
PhysicsComponent holds state only; all logic lives here.
Called at exactly 60 Hz (FIXED_DT) by GameSession.update().
"""

from __future__ import annotations

from core.game_object import Scene
from core.components import PhysicsComponent
from core.primitives import Vec2, Rect2


class PhysicsSystem:

    def update(self, dt: float, scene: Scene) -> None:
        platforms = scene.find_by_tag("platform")

        for obj in scene.all_objects():
            phys = obj.get_component(PhysicsComponent)
            if phys is None or not obj.active or phys.immovable:
                continue

            # Snapshot current position for render interpolation
            obj.prev_position = Vec2(obj.position.x, obj.position.y)

            # Gravity (only while airborne)
            if not phys.is_grounded:
                phys.velocity.y = min(
                    phys.velocity.y + phys.gravity * dt,
                    phys.max_fall_speed,
                )

            # Horizontal friction (only while grounded)
            if phys.is_grounded:
                phys.velocity.x *= 1.0 - phys.friction
                if abs(phys.velocity.x) < 0.5:
                    phys.velocity.x = 0.0

            # Integrate velocity → position
            obj.position.x += phys.velocity.x * dt
            obj.position.y += phys.velocity.y * dt

            # Platform resolution
            was_grounded    = phys.is_grounded
            phys.is_grounded = False

            for platform in platforms:
                from objects.platform import Platform
                if isinstance(platform, Platform):
                    self._resolve_platform(obj, phys, platform, was_grounded)

            # Callbacks
            if phys.is_grounded and not was_grounded and phys.on_landed:
                phys.on_landed()
            elif not phys.is_grounded and was_grounded and phys.on_fell:
                phys.on_fell()

    def _resolve_platform(
        self, obj, phys: PhysicsComponent, platform, was_grounded: bool
    ) -> None:
        from objects.platform import Platform
        p: Platform = platform

        feet_y = obj.position.y
        feet_x = obj.position.x
        half_w = 16.0

        in_x     = p.rect.x - half_w < feet_x < p.rect.x + p.rect.width + half_w
        crossing = obj.prev_position.y <= p.rect.y <= feet_y

        if p.one_way:
            if phys.velocity.y >= 0 and crossing and in_x:
                obj.position.y   = p.rect.y
                phys.velocity.y  = 0.0
                phys.is_grounded = True
        else:
            entity_rect = Rect2(feet_x - half_w, feet_y - 64, half_w * 2, 64)
            if entity_rect.overlaps(p.rect):
                if phys.velocity.y >= 0 and crossing and in_x:
                    obj.position.y   = p.rect.y
                    phys.velocity.y  = 0.0
                    phys.is_grounded = True
