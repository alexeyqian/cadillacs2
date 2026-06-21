"""
systems/camera_system.py
=========================
Follows players, applies lookahead, clamps to bounds, drives screen shake.
"""

from __future__ import annotations

from core.game_object import Scene
from core.primitives import Vec2
from systems.render_system import Camera


class CameraSystem:

    def __init__(
        self,
        lookahead_dist: float = 60.0,
        follow_speed: float = 8.0,
        trauma_decay: float = 1.2,
    ) -> None:
        self.lookahead_dist = lookahead_dist
        self.follow_speed   = follow_speed
        self.trauma_decay   = trauma_decay
        self._lock_x: float | None = None # None = free scroll

    def on_attach(self, bus) -> None:
        bus.on("camera:lock", self._on_lock)
        bus.on("camera:unlock", self._on_unlock)
        bus.on("damage:taken", self._on_damage)
        bus.on("object:died",  self._on_death)
        self._camera: Camera | None = None

    def _on_lock(self, payload) -> None:
        self._lock_x = payload["limit_x"]
        
    def _on_unlock(self, payload) -> None:
        self._lock_x = None

    def _on_damage(self, payload) -> None:
        if self._camera and payload.get("target") and \
           payload["target"].has_tag("player"):
            amount = payload.get("amount", 0)
            self._camera.trauma = min(1.0, self._camera.trauma + amount / 50.0)

    def _on_death(self, payload) -> None:
        if self._camera and payload.get("object") and \
           payload["object"].has_tag("player"):
            self._camera.trauma = min(1.0, self._camera.trauma + 0.8)

    def update(self, dt: float, scene: Scene, camera: Camera) -> None:
        self._camera = camera
        players = scene.find_by_tag("player")
        alive = [p for p in players if getattr(p, "is_alive", True)]
        if not alive:
            return

        # Target = average position of all living players
        avg_x = sum(p.position.x for p in alive) / len(alive)
        avg_y = sum(p.position.y for p in alive) / len(alive)

        # Lookahead: shift target toward player's facing direction
        for p in alive:
            facing = 1.0 if getattr(p, "facing_right", True) else -1.0
            avg_x += facing * self.lookahead_dist / len(alive)

        # Only follow X — Y is depth in world space, not a scroll axis
        t = min(1.0, self.follow_speed * dt)
        camera.position.x += (avg_x - camera.position.x) * t

        camera.clamp_to_bounds()
        camera.apply_shake(dt, self.trauma_decay)

        # Enforce scroll lock
        if self._lock_x is not None:
            camera.position.x = min(camera.position.x, self._lock_x)
