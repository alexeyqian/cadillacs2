"""
systems/pickup_system.py
=========================
AABB overlap test between players and Pickup objects each frame.
Applies ItemData effect and destroys the pickup.
"""

from __future__ import annotations

from core.game_object import Scene
from core.components import CollisionComponent


class PickupSystem:
    """
    Effect types (from ItemData.effect_type):
        'heal'    → player.health.heal(amount)
        'score'   → emits score:changed with bonus
        'powerup' → adds stats bonus for duration seconds
        'life'    → GameStateManager.add_life()
    """

    def __init__(self) -> None:
        self._bus = None
        self._gsm = None   # GameStateManager reference

    def on_attach(self, bus, game_state_manager=None) -> None:
        self._bus = bus
        self._gsm = game_state_manager

    def update(self, dt: float, scene: Scene) -> None:
        players  = scene.find_by_tag("player")
        pickups  = scene.find_by_tag("pickup")

        for player in players:
            pcol = player.get_component(CollisionComponent)
            if pcol is None:
                continue
            player_box = pcol.world_hurtbox()

            for pickup in list(pickups):
                from objects.pickup import Pickup
                if not isinstance(pickup, Pickup):
                    continue
                if pickup.destroyed:
                    continue
                if player_box.overlaps(pickup.trigger_zone()):
                    self._apply(player, pickup, scene)
                    scene.destroy(pickup)

    def _apply(self, player, pickup, scene: Scene) -> None:
        from objects.pickup import Pickup
        p: Pickup = pickup
        item = p.item_data

        if item.effect_type == "heal":
            player.health.heal(int(item.effect_value))

        elif item.effect_type == "score":
            if self._bus:
                self._bus.emit("score:changed", {
                    "score": int(item.effect_value),
                    "delta": int(item.effect_value),
                })

        elif item.effect_type == "powerup":
            stat, val = item.effect_stat, item.effect_value
            if stat and hasattr(player, "stats"):
                player.stats.bonuses[stat] = \
                    player.stats.bonuses.get(stat, 0.0) + val

        elif item.effect_type == "life":
            if self._gsm:
                self._gsm.lives += 1

        if self._bus:
            self._bus.emit("pickup:collected", {
                "collector": player,
                "item_id":   item.id,
            })
