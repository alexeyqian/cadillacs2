# src/core/paths.py
from pathlib import Path

SRC_DIR     = Path(__file__).parent          # .../src/
CONTENT_DIR = SRC_DIR / "content"            # .../src/content/
SPRITES_DIR = CONTENT_DIR / "sprites"        # .../src/content/sprites/
LEVELS_DIR  = CONTENT_DIR / "levels"         # .../src/content/levels/
ENEMIES_DIR = CONTENT_DIR / "enemies"        # .../src/content/enemies/
ITEMS_DIR   = CONTENT_DIR / "items"          # .../src/content/items/
AUDIO_DIR   = CONTENT_DIR / "audio"          # .../src/content/audio/