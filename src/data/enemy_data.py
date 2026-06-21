"""
data/enemy_data.py
==================
EnemyData dataclass and factory that creates configured Enemy instances.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from core.components import CharacterStats
from core.character import AttackDef
from core.player_enemy import DropEntry
from core.primitives import Vec2


@dataclass
class EnemyData:
    id: str
    display_name: str
    move_speed: float
    jump_force: float
    attack_power: float
    defense: float
    recovery_frames: int
    max_health: int
    ai_type: str              # 'brawler' | 'patrol' | 'ranged' | 'boss'
    xp_reward: int
    sprite_atlas: str
    death_vfx: str
    attacks: list[dict] = field(default_factory=list)
    drops: list[dict] = field(default_factory=list)


ENEMY_REGISTRY: dict[str, EnemyData] = {}


def load_enemies(path: str) -> None:
    with open(path) as f:
        raw = json.load(f)
    for entry in raw:
        data = EnemyData(**entry)
        ENEMY_REGISTRY[data.id] = data


class EnemyFactory:
    """
    Creates fully-configured Enemy instances from EnemyData.
    SpawnSystem calls create(enemy_id, position) — the only place
    that knows how to instantiate enemies from data.
    """

    def __init__(self, id_counter_start: int = 1000) -> None:
        self._counter = id_counter_start

    def create(self, enemy_id: str, position: Vec2):
        from core.player_enemy import Enemy
        data = ENEMY_REGISTRY.get(enemy_id)
        if data is None:
            raise KeyError(f"Unknown enemy id: {enemy_id!r}")

        stats = CharacterStats(
            move_speed=data.move_speed,
            jump_force=data.jump_force,
            attack_power=data.attack_power,
            defense=data.defense,
            recovery_frames=data.recovery_frames,
        )

        entity_id = f"enemy_{enemy_id}_{self._counter}"
        self._counter += 1

        enemy = Enemy(entity_id, data.id, stats, data.max_health, data.xp_reward)
        enemy.position = Vec2(position.x, position.y)

        # Register attacks
        for atk in data.attacks:
            enemy.combat.register_attack(AttackDef(
                id=atk["id"],
                startup_frames=atk["startup_frames"],
                active_frames=atk["active_frames"],
                recovery_frames=atk["recovery_frames"],
                base_damage=atk["base_damage"],
                knockback=Vec2(atk.get("kb_x", 0), atk.get("kb_y", 0)),
                can_combo=atk.get("can_combo", True),
            ))

        # Drop table
        for drop in data.drops:
            from core.player_enemy import DropEntry
            enemy.drop_table.drops.append(
                DropEntry(drop["item_id"], drop["quantity"], drop["probability"])
            )

        # AI strategy
        strategy = self._make_strategy(data.ai_type)
        enemy.set_strategy(strategy)

        return enemy

    def _make_strategy(self, ai_type: str):
        from ai.brawler_ai import BrawlerAI
        from ai.patrol_ai import PatrolAI
        from ai.ranged_ai import RangedAI
        from ai.boss_ai import BossAI
        return {
            "brawler": BrawlerAI,
            "patrol":  PatrolAI,
            "ranged":  RangedAI,
            "boss":    BossAI,
        }.get(ai_type, BrawlerAI)()
