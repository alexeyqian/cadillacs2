"""
managers/game_state_manager.py
================================
Top-level application FSM: MainMenu → Playing → Paused → GameOver → Victory.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable


class GameState(Enum):
    MAIN_MENU = auto()
    PLAYING   = auto()
    PAUSED    = auto()
    GAME_OVER = auto()
    VICTORY   = auto()


class GameStateManager:
    """
    State pattern at the application level.
    Transitions trigger scene loads or UI changes via callbacks.
    """

    def __init__(self) -> None:
        self.state: GameState = GameState.MAIN_MENU
        self.lives: int = 3
        self._on_transition: dict[tuple[GameState, GameState], Callable] = {}

    def on_transition(self, from_state: GameState, to_state: GameState, callback: Callable) -> None:
        self._on_transition[(from_state, to_state)] = callback

    def transition(self, new_state: GameState) -> None:
        key = (self.state, new_state)
        self.state = new_state
        if key in self._on_transition:
            self._on_transition[key]()

    def add_life(self) -> None:
        self.lives += 1

    def lose_life(self) -> None:
        self.lives -= 1
        if self.lives <= 0:
            self.transition(GameState.GAME_OVER)

    def on_attach(self, bus) -> None:
        bus.on("object:died", self._on_player_died)
        bus.on("level:complete", self._on_level_complete)

    def _on_player_died(self, payload) -> None:
        obj = payload.get("object")
        if obj and obj.has_tag("player") and self.state == GameState.PLAYING:
            self.lose_life()

    def _on_level_complete(self, payload) -> None:
        if self.state == GameState.PLAYING:
            self.transition(GameState.VICTORY)
