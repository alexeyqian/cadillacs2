"""
systems/collision_system.py
============================
Tests active hitboxes against hurtboxes each frame.
Prevents multi-hitting via a per-attack connected-set.
"""

from __future__ import annotations

from core.game_object import Scene
from core.components import CollisionComponent, DamageInfo
from core.character import Character
from core.primitives import Vec2


class CollisionSystem:
    """
    Each frame:
      1. Collect attackers (Characters with active hitboxes).
      2. Test each hitbox against all opposing hurtboxes.
      3. On overlap: apply damage, register_hit for combo, emit events.

    Multi-hit prevention:
      _connected tracks (attacker_id, hitbox_id, target_id) tuples.
      Cleared when the hitbox deactivates (phase leaves "active").
    """

    def __init__(self) -> None:
        # Set of (attacker_id, hitbox_id, target_id) that already connected
        self._connected: set[tuple[str, str, str]] = set()
        # Previous attack phases to detect deactivation
        self._prev_phases: dict[str, str] = {}

    def update(self, dt: float, scene: Scene) -> None:
        characters = [o for o in scene.all_objects() if isinstance(o, Character)]

        for attacker in characters:
            col = attacker.get_component(CollisionComponent)
            if col is None:
                continue

            # Detect phase transition out of "active" → clear connected set
            prev = self._prev_phases.get(attacker.id, "idle")
            curr = attacker.combat.atk_phase
            if prev == "active" and curr != "active":
                # Remove all entries for this attacker
                self._connected = {
                    t for t in self._connected if t[0] != attacker.id
                }
            self._prev_phases[attacker.id] = curr

            for hitbox in col.get_active_hitboxes():
                hw = col.world_hitbox(hitbox)

                for target in characters:
                    if target is attacker:
                        continue
                    # Only hit opposing teams
                    if attacker.has_tag("player") and target.has_tag("player"):
                        continue
                    if attacker.has_tag("enemy") and target.has_tag("enemy"):
                        continue

                    key = (attacker.id, hitbox.id, target.id)
                    if key in self._connected:
                        continue

                    tcol = target.get_component(CollisionComponent)
                    if tcol is None:
                        continue

                    if hw.overlaps(tcol.world_hurtbox()):
                        self._connected.add(key)

                        # Compute knockback direction (toward target from attacker)
                        dx = target.position.x - attacker.position.x
                        kb_dir = 1.0 if dx >= 0 else -1.0
                        kb = Vec2(hitbox.knockback.x * kb_dir, hitbox.knockback.y)

                        from core.components import StatsComponent
                        stats = attacker.get_component(StatsComponent)
                        power = stats.get("attack_power") if stats else 1.0
                        dmg_amount = hitbox.damage * power

                        info = DamageInfo(
                            amount=dmg_amount,
                            source=attacker,
                            knockback=kb,
                        )
                        target.take_damage(info)
                        attacker.combat.register_hit(target)

                        # Apply knockback component if present
                        from components.knockback_component import KnockbackComponent
                        kb_comp = target.get_component(KnockbackComponent)
                        if kb_comp:
                            kb_comp.apply(kb, freeze_frames=3, stun_frames=12)

                        scene.event_bus.emit("damage:dealt", {
                            "instigator": attacker,
                            "target": target,
                            "amount": dmg_amount,
                        })

                        if col.on_hit:
                            col.on_hit(hitbox, target)
