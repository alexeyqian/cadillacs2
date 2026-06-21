"""
ui/hud.py
=========
Persistent screen-space overlay: HP bars, score, lives.
Subscribes to events — never holds direct references to game objects.
"""

from __future__ import annotations


class HUD:
    """
    Drawn in screen space (Pass 2 — no camera offset).
    Tagged 'screen_ui' so RenderSystem calls draw() each frame.

    Subscribes to:
        damage:taken  → update HP bar for matching player slot
        score:changed → update score display
        object:died   → show lives remaining if player died
    """

    def __init__(self, num_players: int = 1) -> None:
        self.num_players = num_players
        self._hp: dict[int, tuple[int, int]] = {}   # player_index → (current, max)
        self._score: int = 0
        self._lives: int = 3

    def on_attach(self, bus) -> None:
        bus.on("damage:taken",  self._on_damage)
        bus.on("score:changed", self._on_score)
        bus.on("object:died",   self._on_death)

    def _on_damage(self, payload) -> None:
        target = payload.get("target")
        if target and target.has_tag("player"):
            idx = getattr(target, "player_index", 0)
            h   = target.health
            self._hp[idx] = (h.current_health, h.max_health)

    def _on_score(self, payload) -> None:
        self._score = payload.get("score", self._score)

    def _on_death(self, payload) -> None:
        obj = payload.get("object")
        if obj and obj.has_tag("player"):
            self._lives = max(0, self._lives - 1)

    def draw(self, screen_w: int, screen_h: int) -> None:
        """
        Called by RenderSystem._draw_screen_ui() each frame.
        Replace body with backend-specific draw calls.

        Layout:
            Top-left   : HP bars per player
            Top-right  : Score + lives counter
        """
        # Example layout hints (no actual rendering here):
        # for idx, (cur, mx) in self._hp.items():
        #     bar_x = 20
        #     bar_y = 20 + idx * 40
        #     pct   = cur / mx if mx > 0 else 0
        #     draw_rect(bar_x, bar_y, 200, 18, color=RED)
        #     draw_rect(bar_x, bar_y, int(200 * pct), 18, color=GREEN)
        #
        # draw_text(f"SCORE {self._score:07d}", screen_w - 20, 20, align='right')
        # draw_text(f"LIVES {self._lives}", screen_w - 20, 44, align='right')
        pass
