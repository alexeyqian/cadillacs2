"""
systems/vfx_system.py
======================
Subscribes to events and spawns VFXObjects from a pool.
The only class that maps event types to visual effects.
"""

from __future__ import annotations

from core.game_object import Scene
from core.primitives import Vec2


class VFXSystem:
    """
    All other systems fire events and forget.
    VFXSystem is the only subscriber that knows which visual
    effect corresponds to which game event.

    Subscribes to:
        damage:taken     → hit spark at target position
        object:died      → death explosion
        combo:hit        → combo burst at player position
        pickup:collected → pickup sparkle
    """

    def __init__(self, pool: "ObjectPool") -> None:  # type: ignore[name-defined]
        self._pool = pool
        self._scene: Scene | None = None

    def on_attach(self, bus, scene: Scene) -> None:
        self._scene = scene
        bus.on("damage:taken",     self._on_damage)
        bus.on("object:died",      self._on_death)
        bus.on("combo:hit",        self._on_combo)
        bus.on("pickup:collected", self._on_pickup)

    def _on_damage(self, payload) -> None:
        target = payload.get("target")
        if target and self._scene:
            self._spawn_vfx("hit_spark", target.position)

    def _on_death(self, payload) -> None:
        obj = payload.get("object")
        if obj and self._scene:
            self._spawn_vfx("death_explosion", obj.position)

    def _on_combo(self, payload) -> None:
        player = payload.get("player")
        if player and self._scene:
            self._spawn_vfx("combo_burst", player.position)

    def _on_pickup(self, payload) -> None:
        collector = payload.get("collector")
        if collector and self._scene:
            self._spawn_vfx("pickup_sparkle", collector.position)

    def _spawn_vfx(self, vfx_id: str, position: Vec2) -> None:
        if self._scene is None:
            return
        from objects.vfx_object import VFXObject
        vfx: VFXObject = self._pool.acquire()
        vfx.position = Vec2(position.x, position.y)
        vfx.setup(vfx_id)
        self._scene.spawn(vfx)

    def update(self, dt: float, scene: Scene) -> None:
        pass
