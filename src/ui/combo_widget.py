"""
ui/combo_widget.py
==================
Combo counter with decay timer bar.
Shown only while a combo is active.
"""

from __future__ import annotations


class ComboWidget:
    """
    Subscribes to:
        combo:hit   → update count, reset timer, trigger punch-in scale anim
        object:died → reset if player died

    Visual layout (bottom-centre of screen):
        Large combo number
        Thin bar showing time remaining before combo breaks
    """

    def __init__(self, combo_window: float = 0.5) -> None:
        self.combo_window   = combo_window
        self._combo_count   = 0
        self._timer         = 0.0
        self._scale         = 1.0    # punch-in animation scale
        self._active        = False

    def on_attach(self, bus) -> None:
        bus.on("combo:hit",   self._on_combo)
        bus.on("object:died", self._on_death)

    def _on_combo(self, payload) -> None:
        self._combo_count = payload.get("combo_count", self._combo_count)
        self._timer       = self.combo_window
        self._scale       = 1.4    # punch-in: scale up, then decay in update()
        self._active      = True

    def _on_death(self, payload) -> None:
        obj = payload.get("object")
        if obj and obj.has_tag("player"):
            self._reset()

    def _reset(self) -> None:
        self._combo_count = 0
        self._timer       = 0.0
        self._active      = False

    def update(self, dt: float) -> None:
        if not self._active:
            return
        self._timer -= dt
        if self._timer <= 0:
            self._reset()
            return
        # Decay punch-in scale back to 1.0
        self._scale = max(1.0, self._scale - dt * 4.0)

    def draw(self, screen_w: int, screen_h: int) -> None:
        """
        Replace with backend draw calls.

        cx = screen_w // 2
        cy = screen_h - 80
        draw_text(f"{self._combo_count} HIT", cx, cy, scale=self._scale, align='center')
        bar_w = 120
        pct   = self._timer / self.combo_window
        draw_rect(cx - bar_w//2, cy + 28, bar_w, 4, color=GRAY)
        draw_rect(cx - bar_w//2, cy + 28, int(bar_w * pct), 4, color=YELLOW)
        """
        pass
