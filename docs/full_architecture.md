# Beat-Em-Up Architecture

## Layer overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — ENGINE CORE                                                      │
│                                                                             │
│  primitives.py          Vec2 · Rect2 · CollisionLayer · EventBus            │
│  component_base.py      ComponentBase(ABC)                                  │
│  game_object.py         Transform2D · GameObject · Scene                   │
│  components.py          HealthComponent · PhysicsComponent                  │
│                         CollisionComponent · StateMachineComponent          │
│                         AnimationComponent · StatsComponent                 │
│  character.py           AttackDef · CombatComponent · Character             │
│  player_enemy.py        InputProvider · Player                              │
│                         AIStrategy · Enemy                                  │
└─────────────────────────────────────────────────────────────────────────────┘
          ↓ depended on by all layers below
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2 — ENGINE SYSTEMS  (stateless · one update() per frame)             │
│                                                                             │
│  physics_system.py      integrate velocity · gravity · platform resolve     │
│  collision_system.py    hitbox vs hurtbox · multi-hit prevention            │
│  render_system.py       Y-sort · two-pass draw · render interpolation       │
│  camera_system.py       smooth follow · lookahead · screen shake            │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3 — GAME COMPONENTS  (attached to GameObjects)                       │
│                                                                             │
│  sprite_component.py    atlas · frame size · draw offset · color tint       │
│  knockback_component.py freeze frames · hit-stun · knockback launch         │
│  hurt_flash_component.py white/red flash on hit                             │
│  shadow_component.py    blob shadow · scales with air height                │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 4 — GAME OBJECTS  (concrete GameObject subclasses)                   │
│                                                                             │
│  pickup.py              collectible · trigger zone · bob animation          │
│  platform.py            static geometry · solid or one-way                  │
│  projectile.py          owner · velocity · TTL · self-destruct              │
│  trigger.py             zone · named event · one-shot option                │
│  vfx_object.py          pooled · one animation · auto-release               │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 5 — GAME SYSTEMS  (subscribe to events · coordinate state)           │
│                                                                             │
│  spawn_system.py        wave triggers · enemy factory · wave tracking       │
│  score_system.py        damage points · kill bonus · combo multiplier       │
│  pickup_system.py       overlap test · apply ItemData effect                │
│  vfx_system.py          event → VFXObject from pool                        │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 6 — MANAGERS  (cross-scene singletons · persistent state)            │
│                                                                             │
│  game_state_manager.py  MainMenu·Playing·Paused·GameOver·Victory FSM        │
│  level_manager.py       load JSON · populate scene · transition             │
│  audio_manager.py       SFX pool · BGM crossfade · event subscriptions      │
│  save_manager.py        the only class that reads / writes files            │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 7 — UI  (screen-space · separate render pass · no camera offset)     │
│                                                                             │
│  hud.py                 HP bars · score · lives                             │
│  enemy_health_bar.py    world-anchored · fade after 2 s                     │
│  combo_widget.py        combo count · decay bar · punch-in scale            │
│  damage_number.py       pooled · float up · colour-coded · fade out         │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│  LAYER 8 — DATA / CONFIG  (plain dataclasses · loaded from JSON)            │
│                                                                             │
│  item_data.py           ItemData · ITEM_REGISTRY · load_items()             │
│  enemy_data.py          EnemyData · ENEMY_REGISTRY · EnemyFactory           │
│  level_data.py          LevelData · WaveEntry                               │
│  object_pool.py         ObjectPool — reuse VFX/projectile/damage nums       │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│  AI STRATEGIES  (Strategy pattern · hot-swappable on Enemy)                 │
│                                                                             │
│  brawler_ai.py          walk toward player · attack in range                │
│  patrol_ai.py           walk patrol route · aggro on vision                 │
│  ranged_ai.py           maintain distance · throw projectiles               │
│  boss_ai.py             phase transitions at HP thresholds                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Class hierarchy

```
object
└── GameObject                          core/game_object.py
    ├── Character                       core/character.py
    │   ├── Player                      core/player_enemy.py
    │   └── Enemy                       core/player_enemy.py
    ├── Pickup                          objects/pickup.py
    ├── Platform                        objects/platform.py
    ├── Projectile                      objects/projectile.py
    ├── Trigger                         objects/trigger.py
    ├── VFXObject                       objects/vfx_object.py
    ├── EnemyHealthBar   (world UI)     ui/enemy_health_bar.py
    └── DamageNumber     (pooled UI)    ui/damage_number.py

ComponentBase  (ABC)                    core/component_base.py
├── HealthComponent                     core/components.py
├── PhysicsComponent                    core/components.py
├── CollisionComponent                  core/components.py
├── StateMachineComponent               core/components.py
├── AnimationComponent                  core/components.py
├── StatsComponent                      core/components.py
├── InventoryComponent                  core/player_enemy.py
├── ExperienceComponent                 core/player_enemy.py
├── DropTableComponent                  core/player_enemy.py
├── PerceptionComponent                 core/player_enemy.py
├── SpriteComponent                     components/sprite_component.py
├── KnockbackComponent                  components/knockback_component.py
├── HurtFlashComponent                  components/hurt_flash_component.py
└── ShadowComponent                     components/shadow_component.py

AIStrategy     (plain base)             core/player_enemy.py
├── BrawlerAI                           ai/brawler_ai.py
├── PatrolAI                            ai/patrol_ai.py
├── RangedAI                            ai/ranged_ai.py
└── BossAI                              ai/boss_ai.py

InputProvider  (plain base)             core/player_enemy.py
└── [KeyboardInput / GamepadInput / ReplayInput — user-supplied]
```

---

## File structure

```
src/
│
├── core/                           Layer 1 — engine core
│   ├── primitives.py               Vec2, Rect2, CollisionLayer, EventBus
│   ├── component_base.py           ComponentBase(ABC)
│   ├── game_object.py              Transform2D, GameObject, Scene
│   ├── components.py               Health, Physics, Collision, StateMachine,
│   │                               Animation, Stats, DamageInfo, HitboxDef
│   ├── character.py                AttackDef, CombatComponent, Character
│   ├── player_enemy.py             InputProvider, InventoryComponent,
│   │                               ExperienceComponent, Player,
│   │                               AIStrategy, DropTableComponent,
│   │                               PerceptionComponent, Enemy
│   └── __init__.py
│
├── systems/                        Layers 2 & 5 — stateless processors
│   ├── physics_system.py           PhysicsSystem
│   ├── collision_system.py         CollisionSystem
│   ├── render_system.py            RenderSystem, Camera, AssetCache, DrawCall
│   ├── camera_system.py            CameraSystem
│   ├── spawn_system.py             SpawnSystem
│   ├── score_system.py             ScoreSystem
│   ├── pickup_system.py            PickupSystem
│   ├── vfx_system.py               VFXSystem
│   └── __init__.py
│
├── components/                     Layer 3 — game-specific components
│   ├── sprite_component.py         SpriteComponent
│   ├── knockback_component.py      KnockbackComponent
│   ├── hurt_flash_component.py     HurtFlashComponent
│   ├── shadow_component.py         ShadowComponent
│   └── __init__.py
│
├── objects/                        Layer 4 — concrete game objects
│   ├── pickup.py                   Pickup
│   ├── platform.py                 Platform
│   ├── projectile.py               Projectile
│   ├── trigger.py                  Trigger
│   ├── vfx_object.py               VFXObject
│   └── __init__.py
│
├── managers/                       Layer 6 — cross-scene singletons
│   ├── game_state_manager.py       GameState (enum), GameStateManager
│   ├── level_manager.py            LevelManager
│   ├── audio_manager.py            AudioManager
│   ├── save_manager.py             SaveData, SaveManager
│   └── __init__.py
│
├── ui/                             Layer 7 — screen-space UI
│   ├── hud.py                      HUD
│   ├── enemy_health_bar.py         EnemyHealthBar
│   ├── combo_widget.py             ComboWidget
│   ├── damage_number.py            DamageNumber
│   └── __init__.py
│
├── data/                           Layer 8 — dataclasses + registry + pool
│   ├── item_data.py                ItemData, ITEM_REGISTRY, load_items()
│   ├── enemy_data.py               EnemyData, ENEMY_REGISTRY, EnemyFactory
│   ├── level_data.py               LevelData, WaveEntry
│   ├── object_pool.py              ObjectPool
│   └── __init__.py
│
├── ai/                             AI strategy implementations
│   ├── brawler_ai.py               BrawlerAI
│   ├── patrol_ai.py                PatrolAI
│   ├── ranged_ai.py                RangedAI
│   ├── boss_ai.py                  BossAI
│   └── __init__.py
│
└── content/                        JSON data files (no code)
    ├── enemies/
    │   └── enemies.json            grunt, heavy, boss definitions
    ├── levels/
    │   └── level_01.json           platforms, waves, pickups, exit
    └── items/
        └── items.json              food, potions, coins, powerups
```

---

## Component ownership map

Which components are attached to which GameObjects at construction time.

```
Character.__init__()
    HealthComponent          core — HP, shield, i-frames
    PhysicsComponent         core — velocity, gravity, friction
    CollisionComponent       core — hurtbox, hitboxes, layer/mask
    StateMachineComponent    core — idle/walk/attack/hurt/dead FSM
    AnimationComponent       core — frame, facing, sheet row
    StatsComponent           core — move_speed, jump_force, attack_power, defense

Player (extends Character)
    + InventoryComponent     items bag, use_item()
    + ExperienceComponent    level, XP, on_level_up callback

Enemy (extends Character)
    + DropTableComponent     drops list, roll() on death
    + PerceptionComponent    vision cone, hearing range, detected_targets

[Attached by game code at spawn time, not in __init__]
    SpriteComponent          atlas path, frame size, draw offset, color_mod
    KnockbackComponent       freeze frames, hit-stun, launch velocity
    HurtFlashComponent       white/red flash on damage:taken
    ShadowComponent          blob shadow, ground_y, scale by height
```

---

## Event catalogue

All events emitted on the shared `EventBus`. Every subscriber listed.

| Event | Emitted by | Payload fields | Subscribers |
|---|---|---|---|
| `damage:taken` | `HealthComponent.take_damage()` | `target`, `amount: int`, `source` | `HUD`, `EnemyHealthBar`, `HurtFlashComponent`, `CameraSystem`, `AudioManager` |
| `damage:dealt` | `CollisionSystem` | `instigator`, `target`, `amount: float` | `ScoreSystem` |
| `object:died` | `HealthComponent.take_damage()` | `object`, `killed_by` | `SpawnSystem`, `ScoreSystem`, `VFXSystem`, `AudioManager`, `GameStateManager`, `ComboWidget` |
| `state:changed` | `StateMachineComponent.transition()` | `object`, `from: str`, `to: str` | `AudioManager` |
| `combo:hit` | `CombatComponent.register_hit()` | `player`, `combo_count: int` | `ComboWidget`, `ScoreSystem`, `AudioManager`, `VFXSystem` |
| `pickup:collected` | `PickupSystem` | `collector`, `item_id: str` | `VFXSystem`, `AudioManager` |
| `pickup:spawned` | `Enemy._spawn_drops()` | `source`, `position`, `item_id`, `quantity` | `LevelManager` (instantiates Pickup) |
| `score:changed` | `ScoreSystem` | `score: int`, `delta: int` | `HUD`, `SaveManager` |
| `level:exit` | `Trigger.update()` | `trigger`, `player` | `LevelManager` |
| `level:complete` | `LevelManager` | `level_id: str` | `SaveManager`, `GameStateManager` |

---

## Game loop

```
FIXED_DT = 1 / 60        # physics always steps at exactly 60 Hz

tick(real_dt):
    accumulator += real_dt

    while accumulator >= FIXED_DT:
        # Snapshot positions for render interpolation
        for obj in scene.all_objects():
            obj.prev_position = Vec2(obj.position.x, obj.position.y)

        physics_system.update(FIXED_DT, scene)    # integrate + resolve
        collision_system.update(FIXED_DT, scene)  # hitbox vs hurtbox
        spawn_system.update(FIXED_DT, scene)      # wave triggers
        pickup_system.update(FIXED_DT, scene)     # overlap + apply
        score_system.update(FIXED_DT, scene)      # (no-op; driven by events)
        camera_system.update(FIXED_DT, scene, camera)
        scene.update(FIXED_DT)                    # all GameObjects tick

        accumulator -= FIXED_DT

    # Render at actual display rate (60, 120, 144 Hz …)
    alpha = accumulator / FIXED_DT               # 0.0 → 1.0
    render_system.draw(scene, camera, alpha)      # world pass + UI pass
    camera.apply_shake(real_dt)
```

**Why fixed timestep?**
`CombatComponent` stores attack timing as frame counts (`startup_frames`,
`active_frames`, `recovery_frames`). For these counts to be deterministic
on all hardware, each `update()` call must represent exactly 1/60 s.
Physics and knockback also benefit — gravity and friction produce the same
trajectory on a 30 Hz laptop and a 240 Hz desktop.

**Why render interpolation?**
Without it, an object moving at 5 px/frame appears to jump 5 pixels every
16.7 ms, even on a 144 Hz display. With `alpha`, the renderer lerps between
`prev_position` and `position`, producing smooth sub-pixel motion at any
refresh rate without changing the physics simulation.

---

## Design patterns used

| Pattern | Where | Why |
|---|---|---|
| **Component** | All entities via `ComponentBase` | Compose behaviour — no inheritance explosion |
| **System** | `PhysicsSystem`, `CollisionSystem`, `RenderSystem`, `SpawnSystem`, … | Stateless processors; disable or swap without touching entities |
| **Observer / Event bus** | `EventBus` — all cross-object communication | Entities never hold references to UI, audio, or scoring |
| **State (FSM)** | `StateMachineComponent`, `GameStateManager` | Explicit, auditable transitions for both entity and app state |
| **Strategy** | `AIStrategy` on `Enemy`, `InputProvider` on `Player` | Swap AI brain or input source at runtime without subclassing |
| **Object pool** | `ObjectPool` for `VFXObject`, `Projectile`, `DamageNumber` | No GC spikes during heavy combat |
| **Data-driven** | `EnemyData`, `LevelData`, `ItemData` (JSON) | All tunable values outside code; designers edit JSON, not Python |
| **Null object** | `AIStrategy` default, `InputProvider` default | Safe no-op defaults — no null checks in hot paths |
| **Factory** | `EnemyFactory` | Single place that maps `EnemyData.id` → configured `Enemy` instance |
| **Fixed timestep** | Game loop + `CombatComponent` | Frame-count combat data is deterministic on all hardware |
| **Two-pass render** | `RenderSystem.draw()` | World space (camera offset) and screen space (UI) never mix |
| **Y-sort** | `RenderSystem` draw call sort | `(z_index, position.y)` key gives pseudo-3D depth at zero cost |

---

## Render system Z layers

| Constant | Value | Contents |
|---|---|---|
| `Z_SHADOW` | 0 | `ShadowComponent` blobs — always below everything |
| `Z_WORLD` | 1 | Characters, pickups, platforms with sprites |
| `Z_PROJECTILE` | 2 | Thrown objects — above characters |
| `Z_VFX` | 3 | Hit sparks, death explosions — above projectiles |
| `Z_WORLD_UI` | 5 | `EnemyHealthBar` — world-anchored, camera offset applied |
| `Z_SCREEN_UI` | 10 | `HUD`, `ComboWidget`, `DamageNumber` — screen space, no camera offset |

Within the same `z_index`, objects are sorted by `position.y` (world space).
Higher `y` = lower on screen = drawn later = appears in front.

---

## Data flow for a single punch

```
Player._process_input()
    → player.attack("light")
        → CombatComponent.start_attack("light")
            phase: idle → startup → [4 frames] → active

CollisionSystem.update()
    finds hitbox "light" active on Player
    overlaps Enemy hurtbox
        → enemy.take_damage(DamageInfo)
            → HealthComponent.take_damage()
                → KnockbackComponent.apply()       [freeze 3f, stun 12f]
                → emits "damage:taken"
                    → HUD updates HP bar
                    → EnemyHealthBar shows / resets fade
                    → HurtFlashComponent triggers flash
                    → CameraSystem adds trauma
                    → AudioManager plays hit_sound
        → attacker.combat.register_hit(enemy)
            combo_count += 1
            emits "combo:hit"
                → ComboWidget shows count
                → ScoreSystem adds points × multiplier
                → AudioManager plays combo_hit_N
        → emits "damage:dealt"
            → ScoreSystem adds base points
        → VFXSystem spawns hit_spark at enemy.position
```

---

## AI strategy swap — boss phase transition

```
BossAI.update()
    hp_pct = enemy.health.health_percent

    if phase == 1 and hp_pct <= 0.50:
        phase = 2
        enemy.trigger_phase_transition(
            RangedAI(preferred_dist=180, throw_cooldown=1.0),
            stat_bonuses={"move_speed": 40.0}
        )
        # Enemy now:
        #   - uses RangedAI brain
        #   - stats.bonuses["move_speed"] += 40.0
        #   - all previous behaviour replaced, no subclass needed

    if phase == 2 and hp_pct <= 0.25:
        phase = 3
        enemy.trigger_phase_transition(
            BrawlerAI(aggro_range=600, attack_range=80),
            stat_bonuses={"move_speed": 60.0, "attack_power": 0.5}
        )
```