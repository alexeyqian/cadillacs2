# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the game

```bash
cd src
python main.py
```

The entry point is `src/main.py`. All imports are relative to `src/`, so run from there.

## Architecture — 8-layer stack

The game is a 2D beat-em-up built with a component/system architecture (ECS-adjacent). Layers have strict dependency flow downward.

| Layer | Directory | Role |
|---|---|---|
| 1 — Engine core | `src/core/` | `GameObject`, `Scene`, `EventBus`, `Character`, `Player`, `Enemy` |
| 2 — Engine systems | `src/systems/` | Stateless processors: `PhysicsSystem`, `CollisionSystem`, `RenderSystem`, `CameraSystem` |
| 3 — Components | `src/components/` | Attachable behaviours: `SpriteComponent`, `KnockbackComponent`, `HurtFlashComponent`, `ShadowComponent` |
| 4 — Game objects | `src/objects/` | Concrete entities: `Pickup`, `Projectile`, `Platform`, `Trigger`, `VFXObject` |
| 5 — Game systems | `src/systems/` | Event-driven: `SpawnSystem`, `ScoreSystem`, `PickupSystem`, `VFXSystem` |
| 6 — Managers | `src/managers/` | Cross-scene singletons: `GameStateManager`, `LevelManager`, `AudioManager`, `SaveManager` |
| 7 — UI | `src/ui/` | Screen-space: `HUD`, `EnemyHealthBar`, `ComboWidget`, `DamageNumber` |
| 8 — Data | `src/data/` | Plain dataclasses loaded from JSON: `EnemyData`, `LevelData`, `ItemData`, `ObjectPool` |

AI strategy implementations live in `src/ai/` (`brawler_ai`, `patrol_ai`, `ranged_ai`, `boss_ai`).

Content (JSON data files and sprites) lives in `src/content/`.

## Key design rules

**Systems are stateless** — `PhysicsSystem`, `CollisionSystem`, etc. carry no instance data. They read and write component fields only.

**Event bus as the boundary** — game objects never hold direct references to UI, audio, or scoring. They emit events on `EventBus`; those systems subscribe. See `docs/design.md` for the full event catalogue (`damage:taken`, `object:died`, `combo:hit`, etc.).

**Data-driven content** — all tunable numbers live in JSON under `src/content/`. No magic constants in game logic code.

**Object pooling for hot paths** — `VFXObject`, `Projectile`, and `DamageNumber` use `ObjectPool` (`src/data/object_pool.py`) to avoid GC spikes during heavy combat.

**Fixed timestep** — physics and combat step at exactly 60 Hz (`FIXED_DT = 1/60`). Render runs at the display rate and interpolates between the last two physics positions using `alpha = accumulator / FIXED_DT`.

## Renderer backend

`IRenderer` (`src/systems/render_interface.py`) is the stable contract. The current backend is `PygameRenderer` (`src/backends/pygame_renderer.py`). A stub `my_engine_renderer.py` exists for a future custom backend. Engine code only imports from `render_interface` — never from any backend directly.

Asset paths are resolved via constants in `src/core/paths.py` (`SPRITES_DIR`, `LEVELS_DIR`, etc.).
