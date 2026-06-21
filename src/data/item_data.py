"""
data/item_data.py
=================
ItemData dataclass and a simple registry loaded from JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class ItemData:
    id: str
    name: str
    effect_type: str          # 'heal' | 'score' | 'powerup' | 'life'
    effect_value: float
    effect_stat: str = ""     # for powerup: which stat to boost
    duration: float = 0.0    # for powerup; 0 = instant
    sprite_atlas: str = ""
    pickup_sound: str = ""


# Simple in-memory registry — populated by load_items()
ITEM_REGISTRY: dict[str, ItemData] = {}


def load_items(path: str) -> None:
    """Load items from a JSON file into ITEM_REGISTRY."""
    with open(path) as f:
        raw = json.load(f)
    for entry in raw:
        item = ItemData(**entry)
        ITEM_REGISTRY[item.id] = item
