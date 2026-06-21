"""
objects/vfx_object.py
=====================
Pooled one-shot visual effect. Plays one animation then returns to pool.
"""

from __future__ import annotations

from core.game_object import GameObject
from core.primitives import Vec2


class VFXObject(GameObject):
    """
    Participates in Y-sort automatically (real GameObject).
    VFXSystem calls setup(vfx_id) before spawning.
    """

    def __init__(self, entity_id: str) -> None:
        super().__init__(entity_id, "VFXObject")
        self.pool: "ObjectPool | None" = None  # type: ignore[name-defined]
        self._vfx_id: str = ""
        self.add_tag("renderable")
        self.transform.z_index = 3   # Z_VFX

    def setup(self, vfx_id: str) -> None:
        """Configure for a specific effect type before spawning."""
        self._vfx_id = vfx_id
        self.active  = True
        self.visible = True
        from core.components import AnimationComponent
        anim = self.get_component(AnimationComponent)
        if anim:
            anim.play(vfx_id, force=True)
            anim.on_animation_finished = self._on_finished

    def _on_finished(self, name: str) -> None:
        if self.pool:
            self.pool.release(self)
        elif self.scene:
            self.scene.destroy(self)

    def reset(self) -> None:
        """Called by ObjectPool.release() to prepare for reuse."""
        self.active  = False
        self.visible = False
        self._vfx_id = ""

    def update(self, dt: float) -> None:
        super().update(dt)
