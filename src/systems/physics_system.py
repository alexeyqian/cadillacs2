"""
systems/physics_system.py
==========================
2.5D physics: horizontal + depth movement, jump arc on Z axis.
No gravity on Y — Y is depth into the screen, clamped to the walkable strip.
Gravity only acts on Z (jump height), pulling it back to 0 (ground level).
"""

from __future__ import annotations

from core.game_object import Scene
from core.components import PhysicsComponent
from core.primitives import Vec2


class PhysicsSystem:

    def update(
        self,
        dt: float,
        scene: Scene,
        y_min: float = 0.0,
        y_max: float = 120.0,
    ) -> None:
        for obj in scene.all_objects():
            phys = obj.get_component(PhysicsComponent)
            if phys is None or not obj.active or phys.immovable:
                continue

            # Snapshot positions for render interpolation
            obj.prev_position = Vec2(obj.position.x, obj.position.y)
            phys.prev_z       = phys.z

            grounded = phys.is_grounded

            # Friction on X and Y depth (only while on ground)
            if grounded:
                damp = 1.0 - phys.friction
                phys.velocity.x *= damp
                phys.velocity.y *= damp
                if abs(phys.velocity.x) < 0.5:
                    phys.velocity.x = 0.0
                if abs(phys.velocity.y) < 0.5:
                    phys.velocity.y = 0.0

            # Integrate horizontal and depth
            obj.position.x += phys.velocity.x * dt
            obj.position.y += phys.velocity.y * dt
            obj.position.y  = max(y_min, min(y_max, obj.position.y))

            # Jump arc: gravity pulls vz down; Z is clamped at ground (0)
            if not grounded:
                phys.vz -= phys.jump_gravity * dt
            phys.z += phys.vz * dt
            if phys.z <= 0.0:
                phys.z  = 0.0
                phys.vz = 0.0
