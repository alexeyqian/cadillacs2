"""
factories/player_factory.py
============================
Builds a fully-wired Player from content/players/<config>.json.
Called once at game start; the resulting player is injected into GameSession.
"""

from __future__ import annotations

import json
from pathlib import Path

from core.components import AnimationDef, CharacterStats
from core.character import AttackDef
from core.player_enemy import Player
from core.primitives import Vec2
from components.sprite_component import SpriteComponent
from core.paths import SRC_DIR


class PlayerFactory:

    @classmethod
    def create(
        cls,
        input_provider,
        config_path: str = "content/players/player_01.json",
        player_index: int = 0,
    ) -> Player:
        path = SRC_DIR / config_path
        with open(path) as f:
            cfg = json.load(f)

        stats = CharacterStats(**cfg["stats"])
        player = Player(
            entity_id=f"player_{player_index}",
            player_index=player_index,
            input_provider=input_provider,
            stats=stats,
            max_health=cfg["max_health"],
        )

        # SpriteComponent — atlas + frame size + draw offset
        sprite = SpriteComponent(
            atlas=cfg["sprite_atlas"],
            frame_width=cfg["frame_width"],
            frame_height=cfg["frame_height"],
            draw_offset=Vec2(cfg.get("draw_offset_x", 0.0), cfg.get("draw_offset_y", 0.0)),
        )
        player.add_component(sprite)

        # Register animations from config.
        # Attack rows use frame_durations (tick-based); locomotion rows use fps.
        for anim in cfg["animations"]:
            if "frame_durations" in anim:
                defn = AnimationDef(
                    name=anim["name"],
                    sheet_row=anim["sheet_row"],
                    loop=anim.get("loop", False),
                    frame_durations=anim["frame_durations"],
                )
            else:
                defn = AnimationDef(
                    name=anim["name"],
                    sheet_row=anim["sheet_row"],
                    loop=anim.get("loop", True),
                    frame_count=anim["frame_count"],
                    fps=anim["fps"],
                )
            player.animation.register_animation(defn)
        player.animation.play("idle")

        # Register attack definitions
        for atk in cfg["attacks"]:
            player.combat.register_attack(AttackDef(
                id=atk["id"],
                startup_frames=atk["startup_frames"],
                active_frames=atk["active_frames"],
                recovery_frames=atk["recovery_frames"],
                base_damage=atk["base_damage"],
                knockback=Vec2(atk.get("kb_x", 0.0), atk.get("kb_y", 0.0)),
                can_combo=atk.get("can_combo", True),
            ))

        return player
