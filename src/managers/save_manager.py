"""
managers/save_manager.py
=========================
The only class that reads or writes files.
Everything else notifies SaveManager via events.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class SaveData:
    current_level: int = 0
    high_score: int = 0
    unlocked_characters: list[str] = field(default_factory=list)


class SaveManager:
    """
    Subscribes to:
        score:changed   → update high score if beaten
        level:complete  → increment current_level, save to disk
    """

    def __init__(self, save_path: str = "save.json") -> None:
        self.save_path = save_path
        self.data      = SaveData()

    def on_attach(self, bus) -> None:
        bus.on("score:changed",  self._on_score)
        bus.on("level:complete", self._on_level_complete)

    def _on_score(self, payload) -> None:
        score = payload.get("score", 0)
        if score > self.data.high_score:
            self.data.high_score = score

    def _on_level_complete(self, payload) -> None:
        self.data.current_level += 1
        self.save()

    def save(self) -> None:
        try:
            with open(self.save_path, "w") as f:
                json.dump({
                    "current_level": self.data.current_level,
                    "high_score":    self.data.high_score,
                    "unlocked_characters": self.data.unlocked_characters,
                }, f, indent=2)
        except OSError:
            pass

    def load(self) -> SaveData:
        try:
            with open(self.save_path) as f:
                raw = json.load(f)
            self.data = SaveData(**raw)
        except (FileNotFoundError, KeyError, TypeError):
            self.data = SaveData()
        return self.data
