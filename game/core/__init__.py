"""
__init__.py — public API for the beat-em-up core package.
"""

from .primitives import Vec2, Rect2, CollisionLayer, EventBus
from .component_base import ComponentBase
from .game_object import Transform2D, GameObject, Scene
from .components import (
    DamageInfo,
    HealthComponent,
    PhysicsComponent,
    HitboxDef,
    CollisionComponent,
    State,
    StateMachineComponent,
    AnimationDef,
    AnimationComponent,
    CharacterStats,
    StatsComponent,
)
from .character import AttackDef, CombatComponent, Character
from .player_enemy import (
    InputProvider,
    PickupItem,
    InventoryComponent,
    ExperienceComponent,
    Player,
    AIStrategy,
    DropEntry,
    DropTableComponent,
    PerceptionComponent,
    Enemy,
)

__all__ = [
    "Vec2", "Rect2", "CollisionLayer", "EventBus",
    "ComponentBase",
    "Transform2D", "GameObject", "Scene",
    "DamageInfo", "HealthComponent", "PhysicsComponent",
    "HitboxDef", "CollisionComponent",
    "State", "StateMachineComponent",
    "AnimationDef", "AnimationComponent",
    "CharacterStats", "StatsComponent",
    "AttackDef", "CombatComponent", "Character",
    "InputProvider", "PickupItem", "InventoryComponent", "ExperienceComponent", "Player",
    "AIStrategy", "DropEntry", "DropTableComponent", "PerceptionComponent", "Enemy",
]