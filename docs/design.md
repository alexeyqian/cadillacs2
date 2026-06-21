# 2D Beat-Em-Up — Architecture & Design Document

## Table of contents

1. [Overview](#overview)
2. [Layer diagram](#layer-diagram)
3. [Layer 1 — Engine core (already built)](#layer-1--engine-core-already-built)
4. [Layer 2 — Engine systems](#layer-2--engine-systems)
5. [Layer 3 — New components](#layer-3--new-components)
6. [Layer 4 — Game object classes](#layer-4--game-object-classes)
7. [Layer 5 — Game systems](#layer-5--game-systems)
8. [Layer 6 — Managers](#layer-6--managers)
9. [Layer 7 — UI](#layer-7--ui)
10. [Layer 8 — Data / config](#layer-8--data--config)
11. [Design patterns summary](#design-patterns-summary)
12. [File structure](#file-structure)
13. [Game loop](#game-loop)
14. [Event catalogue](#event-catalogue)

---

## Overview

This document describes the full architecture for a basic playable 2D beat-em-up, building on the entity core (`GameObject`, `Character`, `Player`, `Enemy`) already designed. The architecture is organised into eight layers, each with a clear responsibility boundary. Systems are stateless processors; components own per-entity data; managers own cross-scene state; data classes hold all tunable values in JSON-loadable plain dataclasses.

**Core principles:**

- Composition over inheritance — behaviour comes from attached components, not deep class hierarchies.
- Stateless systems — `PhysicsSystem`, `CollisionSystem`, `RenderSystem` etc. have no fields; they read and write component data only.
- Event bus as the boundary — game objects never hold direct references to UI, audio, or scoring. They emit events; those systems subscribe.
- Data-driven content — all tunable numbers (`EnemyData`, `LevelData`, `AttackDef`) live in JSON files. No magic constants in code.
- Object pooling for hot paths — `VFXObject`, `Projectile`, and `DamageNumber` are pooled to avoid GC spikes during heavy combat.

---

## Layer diagram

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1 — ENGINE CORE  (already built)                     │
│  GameObject · Character · Player · Enemy                    │
│  ComponentBase · Scene · EventBus                           │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2 — ENGINE SYSTEMS  (stateless, process all objects) │
│  PhysicsSystem · CollisionSystem · RenderSystem             │
│  CameraSystem                                               │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3 — NEW COMPONENTS  (attached to GameObjects)        │
│  SpriteComponent · KnockbackComponent                       │
│  HurtFlashComponent · ShadowComponent                       │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4 — GAME OBJECT CLASSES                              │
│  Pickup · Projectile · Platform · Door/Trigger · VFXObject  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  LAYER 5 — GAME SYSTEMS  (subscribe to events)              │
│  SpawnSystem · ScoreSystem · PickupSystem · VFXSystem       │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  LAYER 6 — MANAGERS  (cross-scene singletons)               │
│  GameStateManager · LevelManager · AudioManager             │
│  SaveManager                                                │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  LAYER 7 — UI  (screen-space, separate render pass)         │
│  HUD · EnemyHealthBar · ComboWidget · DamageNumber          │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  LAYER 8 — DATA / CONFIG  (plain dataclasses from JSON)     │
│  EnemyData · LevelData · AttackData · ItemData · ObjectPool │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Engine core (already built)

| Class | File | Responsibility |
|---|---|---|
| `Vec2`, `Rect2`, `CollisionLayer`, `EventBus` | `primitives.py` | Value types and event bus |
| `ComponentBase` | `component_base.py` | Single base class for all components |
| `Transform2D`, `GameObject`, `Scene` | `game_object.py` | Root entity and scene container |
| `HealthComponent`, `PhysicsComponent`, `CollisionComponent`, `StateMachineComponent`, `AnimationComponent`, `StatsComponent` | `components.py` | Shared reusable components |
| `AttackDef`, `CombatComponent`, `Character` | `character.py` | Combat-capable entity base |
| `InputProvider`, `InventoryComponent`, `ExperienceComponent`, `Player` | `player_enemy.py` | Human-controlled character |
| `AIStrategy`, `DropTableComponent`, `PerceptionComponent`, `Enemy` | `player_enemy.py` | AI-controlled character |

**Key design decisions already made:**

- `CombatComponent` is a plain class, not a `ComponentBase` subclass — no scene lifecycle needed, easier to unit-test.
- HP fields are `int`; `DamageInfo.amount` is `float` (pre-reduction). `take_damage()` returns `int` with `math.floor` rounding.
- Frame counts are the authoring unit for `AttackDef` (designer-friendly); internally converted to seconds for the `dt` update loop.
- No `I`-prefix interface classes — `ComponentBase(ABC)` with `@abstractmethod` enforces the contract directly.

---

## Layer 2 — Engine systems

Systems are **stateless classes** with a single `update(dt, scene)` method. They read and write component data but own no instance state. This is the System half of the ECS-adjacent pattern that Unity and Godot both converge on.

### PhysicsSystem

```python
class PhysicsSystem:
    """
    1. Integrate velocity → position for all PhysicsComponent owners.
    2. Resolve overlaps against Platform colliders (AABB sweep).
    3. Set is_grounded flag; fire on_landed / on_fell callbacks.

    Design note: always separate integration (move) from resolution
    (push apart). Mixing them inside PhysicsComponent.update() causes
    tunnelling and order-dependent jitter.
    """

    def update(self, dt: float, scene: Scene) -> None: ...
```

**Fixed timestep** — the game loop calls `PhysicsSystem.update(FIXED_DT)` at a locked 60 Hz regardless of render frame rate. This makes frame-count combat data deterministic on all hardware.

### CollisionSystem

```python
class CollisionSystem:
    """
    Each frame:
      - Collect all active HitboxDefs from Characters with CombatComponent.
      - Test each hitbox against all hurtboxes on the opposing team.
      - On overlap: call combat.register_hit(target), emit 'damage:dealt'.
      - Track which (attacker, hitbox_id, target) pairs already connected
        this attack to prevent multi-hitting within one active window.

    Optimisation: spatial grid partitioned by x-position.
    Only test hitboxes against hurtboxes within the same or adjacent cells.
    """

    def update(self, dt: float, scene: Scene) -> None: ...
```

**Multi-hit prevention** — store a `set[tuple[str, str, str]]` of `(attacker_id, hitbox_id, target_id)` that resets when the hitbox deactivates. Without this, a 6-frame active window hits the target 6 times.

### RenderSystem

```python
class RenderSystem:
    """
    1. Collect all visible GameObjects with a SpriteComponent.
    2. Sort by z_index, then by position.y within the same z_index.
       This Y-sort gives beat-em-ups their pseudo-3D depth read.
    3. Draw each sprite at round(position.x - camera.x), round(position.y - camera.y).
    4. Draw ShadowComponents first (always below sprites).
    5. Draw world-space UI (EnemyHealthBar) last in this pass.
    6. Draw screen-space UI (HUD, ComboWidget) in a separate pass
       with no camera offset applied.
    """

    def update(self, dt: float, scene: Scene, camera: Camera) -> None: ...
```

**Render interpolation** — if using a fixed physics timestep, render at `physics_pos + velocity * alpha` where `alpha = accumulator / FIXED_DT`. This eliminates judder at render rates above 60 Hz.

### CameraSystem

```python
class Camera:
    position: Vec2
    bounds: Rect2           # level boundaries — camera never shows outside
    shake_trauma: float     # 0–1; shake intensity = trauma²

@dataclass
class CameraSystem:
    """
    - Smoothly follow the average position of all living Players.
    - Apply lookahead: offset toward the player's facing direction.
    - Clamp to level bounds.
    - Apply trauma-based screen shake (trauma decays over time).

    Subscribes to:
      'damage:taken'  → add trauma proportional to amount
      'object:died'   → large trauma burst if a player dies
    """
    lookahead_dist: float = 60.0
    follow_speed: float = 8.0      # lerp factor per second
    trauma_decay: float = 1.2      # trauma units lost per second

    def update(self, dt: float, scene: Scene) -> None: ...
```

The camera never moves the world — it computes an offset that `RenderSystem` subtracts from every draw call.

---

## Layer 3 — New components

### SpriteComponent

```python
@dataclass
class SpriteComponent(ComponentBase):
    """
    Holds the texture reference and draw metadata.
    AnimationComponent (already built) drives which frame to show.
    SpriteComponent stores the atlas and per-frame offset.
    """
    atlas: str                      # path to sprite sheet
    draw_offset: Vec2               # pivot offset from position
    color_mod: tuple[int,int,int,int] = (255, 255, 255, 255)  # RGBA tint

    def update(self, dt: float) -> None: pass
```

### KnockbackComponent

```python
class KnockbackComponent(ComponentBase):
    """
    Manages hit-stun and knockback separately from PhysicsComponent.

    Why separate from PhysicsComponent:
      - Knockback overrides normal movement and ignores friction.
      - Hit-stun (freeze frames) pauses the entity briefly before
        the knockback launches — a classic beat-em-up feel detail.
      - Regular velocity (walking, jumping) should not be affected
        by the freeze-frame logic.

    Typical sequence:
      1. Hit registered → freeze_frames = 3, knockback_velocity set.
      2. For freeze_frames: zero all velocity, pause animation.
      3. After freeze: apply knockback_velocity to PhysicsComponent.
      4. hit_stun_frames counts down; PhysicsComponent.immovable = True
         during stun so the enemy can't act.
    """
    freeze_frames: int = 0
    hit_stun_frames: int = 0
    knockback_velocity: Vec2 = field(default_factory=Vec2)

    def update(self, dt: float) -> None: ...
```

### HurtFlashComponent

```python
class HurtFlashComponent(ComponentBase):
    """
    Triggers a white-flash on the SpriteComponent for a fixed
    number of frames when the owner takes damage.

    Without this, hits feel soft regardless of sound design.
    Subscribes to owner's HealthComponent.on_damage callback in on_start().
    """
    flash_frames: int = 4
    _remaining: int = 0

    def on_start(self) -> None:
        self.owner.health.on_damage = self._on_damage   # type: ignore

    def _on_damage(self, info: DamageInfo, amount: int) -> None:
        self._remaining = self.flash_frames

    def update(self, dt: float) -> None:
        if self._remaining > 0:
            self._remaining -= 1
            sprite = self.owner.get_component(SpriteComponent)
            if sprite:
                sprite.color_mod = (255, 255, 255, 255) if self._remaining % 2 else (255, 80, 80, 255)
```

### ShadowComponent

```python
class ShadowComponent(ComponentBase):
    """
    Draws a simple ellipse on the ground plane beneath the entity.

    Scale and opacity decrease as position.y decreases (entity is
    higher in the air). This communicates aerial position and creates
    the pseudo-3D depth read essential to the beat-em-up genre.

    Rendered by RenderSystem before the sprite (always below).
    """
    base_width: float = 28.0
    base_height: float = 8.0
    ground_y: float = 0.0   # set to the platform surface Y at spawn

    def update(self, dt: float) -> None: pass

    def get_draw_params(self) -> tuple[float, float, float]:
        """Returns (width, height, alpha) for the renderer."""
        height_above = max(0.0, self.ground_y - self.owner.position.y)
        scale = max(0.3, 1.0 - height_above / 120.0)
        alpha = scale
        return self.base_width * scale, self.base_height * scale, alpha
```

---

## Layer 4 — Game object classes

### Pickup

```python
class Pickup(GameObject):
    """
    Collectible item (food, powerup, coin, etc.).

    Design: Pickup is generic — the effect is entirely data-driven
    via ItemData. The Pickup object itself only handles the overlap
    check and destruction. PickupSystem applies the effect.

    Typical contents:
      - SpriteComponent  (bobbing animation optional)
      - CollisionComponent with layer=PICKUP, mask=PLAYER
    """
    def __init__(self, entity_id: str, item_data: "ItemData") -> None: ...
```

### Projectile

```python
class Projectile(GameObject):
    """
    Owned by a Character; moves at constant velocity; self-destructs
    on TTL expiry or world collision.

    The source reference lets the CollisionSystem attribute damage
    correctly (score, XP, combo tracking).

    Has one active HitboxDef for its lifetime (unlike melee attacks
    which have startup/active/recovery phases).
    """
    source: Character
    velocity: Vec2
    ttl: float                  # seconds until auto-destroy
    _elapsed: float = 0.0

    def update(self, dt: float) -> None:
        self._elapsed += dt
        if self._elapsed >= self.ttl:
            self.scene.destroy(self)
```

### Platform

```python
@dataclass
class Platform(GameObject):
    """
    Static geometry. Not a full entity — no update loop, minimal components.
    PhysicsSystem reads platforms directly via scene.find_by_tag('platform').

    one_way: True  → character can jump through from below (classic
                      beat-em-up floating platforms)
    one_way: False → solid from all sides
    """
    rect: Rect2
    one_way: bool = False
```

### Door / Trigger

```python
class Trigger(GameObject):
    """
    Axis-aligned zone that emits a named event when a Player enters.
    Used for: level exits, cutscene starts, shop entrances, wave triggers.

    SpawnSystem and LevelManager subscribe to the emitted events.
    The Trigger itself is stateless — it only emits, never acts.
    """
    zone: Rect2
    event_name: str             # e.g. 'level:exit', 'cutscene:boss_intro'
    one_shot: bool = True       # destroy after first activation
    _fired: bool = False

    def update(self, dt: float) -> None:
        if self._fired:
            return
        for player in self.scene.find_by_tag('player'):
            if self._overlaps(player.position):
                self.scene.event_bus.emit(self.event_name, {'trigger': self})
                if self.one_shot:
                    self._fired = True
                    self.scene.destroy(self)
                break
```

### VFXObject

```python
class VFXObject(GameObject):
    """
    Pooled one-shot visual effect. Plays one animation, then returns
    to the pool (or destroys itself if pooling is not set up yet).

    Participates in z-sorting automatically because it is a real
    GameObject — no special renderer case needed.
    """
    pool: "ObjectPool | None" = None

    def _on_animation_finished(self, name: str) -> None:
        if self.pool:
            self.pool.release(self)
        else:
            self.scene.destroy(self)
```

---

## Layer 5 — Game systems

### SpawnSystem

```python
class SpawnSystem:
    """
    Reads LevelData.waves and spawns enemies when trigger conditions are met.

    Trigger condition types:
      'on_enter_x:{value}'   — player passes x coordinate
      'on_wave_clear:{index}'— previous wave index is fully defeated
      'on_timer:{seconds}'   — elapsed since level start

    Subscribes to:
      'object:died'  → check if current wave is cleared

    Pattern: each wave is a simple data record; SpawnSystem is the
    only place that knows how to instantiate enemies from EnemyData.
    """

    def __init__(self, level_data: "LevelData", enemy_factory: "EnemyFactory") -> None: ...
    def update(self, dt: float, scene: Scene) -> None: ...
```

### ScoreSystem

```python
class ScoreSystem:
    """
    Listens for combat events and maintains the score independently
    of Player. This keeps co-op scoring and leaderboards trivial to add.

    Subscribes to:
      'damage:dealt' → base points proportional to damage
      'object:died'  → kill bonus, scaled by enemy type
      'combo:hit'    → multiplier applied to recent points

    Emits:
      'score:changed' → HUD subscribes to update the display
    """
    score: int = 0
    high_score: int = 0
```

### PickupSystem

```python
class PickupSystem:
    """
    Each frame: AABB test between each Player's hurtbox and all
    live Pickup objects. On overlap, reads ItemData and applies effect.

    Effect types:
      'heal'      → player.health.heal(amount)
      'score'     → emit 'score:changed' with bonus
      'powerup'   → add StatsComponent bonus for duration seconds
      'life'      → GameStateManager.add_life()

    Emits:
      'pickup:collected' → AudioManager plays sound, VFXSystem spawns fx
    """
    def update(self, dt: float, scene: Scene) -> None: ...
```

### VFXSystem

```python
class VFXSystem:
    """
    Subscribes to events and spawns VFXObjects from a pool.
    The only class that maps event types to visual effects.
    All other systems fire events and forget — they never call VFXSystem.

    Subscribes to:
      'damage:taken'     → hit spark at target position
      'object:died'      → death explosion
      'combo:hit'        → combo burst at player position
      'pickup:collected' → pickup sparkle

    Uses ObjectPool to avoid GC spikes during heavy combat.
    """
    def __init__(self, pool: "ObjectPool") -> None: ...
```

---

## Layer 6 — Managers

Managers are **cross-scene singletons** that own persistent state. Pass them by reference at construction time — do not use global variables.

### GameStateManager

```python
class GameState(Enum):
    MAIN_MENU  = auto()
    PLAYING    = auto()
    PAUSED     = auto()
    GAME_OVER  = auto()
    VICTORY    = auto()

class GameStateManager:
    """
    Top-level FSM for the application.

    Each transition triggers a scene load or UI change:
      MAIN_MENU → PLAYING   : load first level, initialise systems
      PLAYING   → PAUSED    : freeze update loop, show pause menu
      PLAYING   → GAME_OVER : stop music, show game-over screen
      PLAYING   → VICTORY   : play fanfare, show score, save progress

    Pattern: State pattern at the application level.
    Godot equivalent: SceneTree.change_scene()
    Unity equivalent: SceneManager.LoadScene()
    """
    state: GameState = GameState.MAIN_MENU
    lives: int = 3

    def transition(self, new_state: GameState) -> None: ...
```

### LevelManager

```python
class LevelManager:
    """
    Loads LevelData from JSON, instantiates Platforms and background
    layers, hands the wave list to SpawnSystem.

    Also manages the transition sequence between levels:
      1. Fade out.
      2. Destroy current scene.
      3. Load next LevelData.
      4. Populate new scene.
      5. Fade in.

    Subscribes to:
      'level:exit' → begin transition to next level
    """
    current_level: int = 0
    levels: list[str] = field(default_factory=list)  # paths to JSON files
```

### AudioManager

```python
class AudioManager:
    """
    Wraps the audio library with a pooled SFX system and BGM crossfading.

    Gameplay code never calls audio directly — AudioManager subscribes
    to game events and plays the appropriate sound.

    Subscribes to:
      'damage:taken'     → play hit sound (varied pitch)
      'object:died'      → play death sound
      'pickup:collected' → play pickup chime
      'combo:hit'        → play combo hit sound (escalating pitch)
      'state:changed'    → crossfade BGM between combat/calm

    BGM states:
      'calm'   → ambient level music
      'combat' → battle music (crossfade when enemies detected)
      'boss'   → boss battle music
    """
    _sfx_pool: dict[str, list]   # sound_id → pool of audio channels
    _bgm_track: str = ''
```

### SaveManager

```python
@dataclass
class SaveData:
    current_level: int = 0
    high_score: int = 0
    unlocked_characters: list[str] = field(default_factory=list)

class SaveManager:
    """
    The only class that reads or writes files.
    Everything else reads SaveData at startup and notifies
    SaveManager via events — never writes directly.

    Subscribes to:
      'score:changed'  → update high score if beaten
      'level:complete' → increment current_level, save to disk
      'object:died'    → save on player death (anti-cheat checkpoint)
    """
    save_path: str = 'save.json'
    data: SaveData = field(default_factory=SaveData)

    def save(self) -> None: ...
    def load(self) -> SaveData: ...
```

---

## Layer 7 — UI

All UI is drawn in a **separate render pass** after the game world, in screen space (no camera offset applied). UI subscribes to the event bus — it never holds direct references to game objects.

### HUD

```python
class HUD:
    """
    Persistent screen-space overlay.

    Subscribes to:
      'damage:taken'  → update HP bar for the matching player slot
      'score:changed' → update score display
      'combo:hit'     → forward to ComboWidget
      'object:died'   → show 'lives remaining' flash if player died

    Layout (typical beat-em-up):
      Top-left   : Player 1 HP bar + portrait
      Top-right  : Score + lives
      Top-center : Timer (if game has time limit)
      Bottom     : ComboWidget (shown only while combo is active)
    """
```

### EnemyHealthBar

```python
class EnemyHealthBar:
    """
    World-space health bar drawn above each enemy.
    Shown only while the enemy was recently hit (fade out after 2 s).

    Positioned at enemy.position + Vec2(0, -enemy_height - 8).
    Converted to screen space by RenderSystem before drawing.

    Subscribes to:
      'damage:taken' filtered by target → show and reset fade timer
    """
    fade_duration: float = 2.0
```

### ComboWidget

```python
class ComboWidget:
    """
    Displays current combo count with a decay timer bar.

    Visual design: large number centre-screen bottom, shrinking bar
    shows time remaining before combo breaks. Scales up briefly on
    each new hit (punch-in animation).

    Subscribes to:
      'combo:hit'    → update count, reset timer, play punch-in anim
      'object:died'  → reset if player died
    """
    combo_window: float = 0.5    # seconds; must match CombatComponent
```

### DamageNumber

```python
class DamageNumber:
    """
    Pooled floating text spawned at the hit position.
    Floats upward ~40px and fades out over 0.8 s.

    Colour coding:
      White  → normal hit
      Yellow → critical / high damage
      Red    → player takes damage
      Green  → healing

    Spawned by VFXSystem on 'damage:taken'.
    Uses ObjectPool to avoid GC spikes.
    """
    lifetime: float = 0.8
    rise_speed: float = 50.0     # px/s upward
```

---

## Layer 8 — Data / config

All tunable values live in JSON files. Code never contains magic numbers for balance data.

```python
@dataclass
class ItemData:
    id: str
    name: str
    effect_type: str            # 'heal' | 'score' | 'powerup' | 'life'
    effect_value: float
    duration: float = 0.0       # for powerups; 0 = instant
    sprite_atlas: str = ''
    pickup_sound: str = ''

@dataclass
class EnemyData:
    id: str
    display_name: str
    stats: CharacterStats
    max_health: int
    ai_type: str                # 'brawler' | 'patrol' | 'ranged' | 'boss'
    attacks: list[AttackDef]
    drop_table: list[DropEntry]
    sprite_atlas: str
    death_vfx: str
    xp_reward: int

@dataclass
class WaveEntry:
    enemy_id: str
    position: Vec2
    trigger: str                # 'on_enter_x:400' | 'on_wave_clear:0' | 'on_timer:5.0'
    facing_right: bool = False

@dataclass
class LevelData:
    id: str
    display_name: str
    background_layers: list[str]
    music_track: str
    platforms: list[Rect2]
    waves: list[WaveEntry]
    pickups: list[tuple[str, Vec2]]   # (item_id, position)
    exit_position: Vec2
    next_level_id: str | None = None
```

### ObjectPool

```python
class ObjectPool:
    """
    Reusable object pool for VFXObject, Projectile, DamageNumber.

    Avoids GC spikes during heavy combat by pre-allocating a fixed
    set of objects and recycling them rather than constructing new ones.

    Usage:
        pool = ObjectPool(factory=lambda: VFXObject('vfx_hit'), size=32)
        obj = pool.acquire()
        # ... use obj ...
        pool.release(obj)       # returns to pool; calls obj.reset()
    """
    def __init__(self, factory: Callable[[], GameObject], size: int) -> None: ...
    def acquire(self) -> GameObject: ...
    def release(self, obj: GameObject) -> None: ...
```

---

## Design patterns summary

| Pattern | Where used | Why |
|---|---|---|
| **Component** | All entities | Compose behaviour without inheritance explosion |
| **System** | Physics, Collision, Render, Spawn | Stateless processors; easy to disable, test, or swap |
| **Observer / Event bus** | Everything | Decouples game objects from UI, audio, and scoring |
| **State (FSM)** | `StateMachineComponent`, `GameStateManager` | Both entity state and app state need explicit, auditable transitions |
| **Strategy** | `AIStrategy`, `InputProvider` | Swap behaviour at runtime without touching the entity class |
| **Object pool** | `VFXObject`, `Projectile`, `DamageNumber` | Avoid GC spikes in hot combat loops |
| **Data-driven** | `EnemyData`, `LevelData`, `AttackDef` | All tunable values in JSON; designers edit data, not code |
| **Null object** | `AIStrategy` default, `InputProvider` default | Safe no-op defaults eliminate null checks in hot paths |
| **Fixed timestep** | `PhysicsSystem`, `CombatComponent` | Deterministic frame-count combat on variable-rate hardware |
| **Factory** | `EnemyFactory` (used by `SpawnSystem`) | Single place that maps `EnemyData.id` to a configured `Enemy` instance |

---

## File structure

```
src/
├── core/                       # Layer 1 — already built
│   ├── primitives.py           # Vec2, Rect2, CollisionLayer, EventBus
│   ├── component_base.py       # ComponentBase(ABC)
│   ├── game_object.py          # Transform2D, GameObject, Scene
│   ├── components.py           # Health, Physics, Collision, StateMachine, Animation, Stats
│   ├── character.py            # AttackDef, CombatComponent, Character
│   ├── player_enemy.py         # InputProvider, Player, AIStrategy, Enemy
│   └── __init__.py
│
├── systems/                    # Layers 2 & 5 — stateless processors
│   ├── physics_system.py
│   ├── collision_system.py
│   ├── render_system.py
│   ├── camera_system.py
│   ├── spawn_system.py
│   ├── score_system.py
│   ├── pickup_system.py
│   └── vfx_system.py
│
├── components/                 # Layer 3 — new components
│   ├── sprite_component.py
│   ├── knockback_component.py
│   ├── hurt_flash_component.py
│   └── shadow_component.py
│
├── objects/                    # Layer 4 — game object classes
│   ├── pickup.py
│   ├── projectile.py
│   ├── platform.py
│   ├── trigger.py
│   └── vfx_object.py
│
├── managers/                   # Layer 6 — singletons
│   ├── game_state_manager.py
│   ├── level_manager.py
│   ├── audio_manager.py
│   └── save_manager.py
│
├── ui/                         # Layer 7 — screen-space UI
│   ├── hud.py
│   ├── enemy_health_bar.py
│   ├── combo_widget.py
│   └── damage_number.py
│
├── data/                       # Layer 8 — dataclasses + pool
│   ├── item_data.py
│   ├── enemy_data.py
│   ├── level_data.py
│   └── object_pool.py
│
├── ai/                         # AI strategy implementations
│   ├── brawler_ai.py           # walk toward player, attack in range
│   ├── patrol_ai.py            # walk back and forth, aggro on sight
│   ├── ranged_ai.py            # maintain distance, throw projectiles
│   └── boss_ai.py              # phase-based, calls trigger_phase_transition
│
└── content/                    # JSON data files
    ├── enemies/
    │   ├── grunt.json
    │   ├── heavy.json
    │   └── boss.json
    ├── levels/
    │   ├── level_01.json
    │   └── level_02.json
    └── items/
        ├── food.json
        └── powerups.json
```

---

## Game loop

```python
FIXED_DT = 1 / 60          # physics always steps at exactly 60 Hz

class GameLoop:
    def __init__(self, scene: Scene, systems: list) -> None:
        self.scene = scene
        self.systems = systems
        self._accumulator = 0.0

    def tick(self, real_dt: float) -> None:
        """
        Fixed-timestep loop with render interpolation.

        Physics and combat run at locked 60 Hz — frame-count attack data
        is perfectly deterministic.

        Render runs at whatever the platform supports — interpolates
        between the last two physics positions for smooth visuals.
        """
        self._accumulator += real_dt

        # Fixed physics steps
        while self._accumulator >= FIXED_DT:
            self.scene.update(FIXED_DT)         # ticks all GameObjects
            for system in self.systems:
                system.update(FIXED_DT, self.scene)
            self._accumulator -= FIXED_DT

        # Render at actual frame rate, interpolated
        alpha = self._accumulator / FIXED_DT
        render_system.draw(self.scene, alpha)
        ui_system.draw(self.scene)
```

---

## Event catalogue

All events emitted on the shared `EventBus`. Payload fields listed.

| Event | Emitted by | Payload | Subscribers |
|---|---|---|---|
| `damage:taken` | `HealthComponent` | `target`, `amount: int`, `source` | `HUD`, `EnemyHealthBar`, `HurtFlashComponent`, `CameraSystem`, `AudioManager` |
| `damage:dealt` | `CollisionSystem` | `instigator`, `target`, `amount: int` | `ScoreSystem` |
| `object:died` | `HealthComponent` | `object`, `killed_by` | `SpawnSystem`, `ScoreSystem`, `VFXSystem`, `AudioManager`, `GameStateManager` |
| `state:changed` | `StateMachineComponent` | `object`, `from: str`, `to: str` | `AnimationComponent` (drives anim), `AudioManager` |
| `combo:hit` | `CombatComponent` | `player`, `combo_count: int` | `ComboWidget`, `ScoreSystem`, `AudioManager` |
| `pickup:collected` | `PickupSystem` | `collector`, `item_id: str` | `VFXSystem`, `AudioManager` |
| `pickup:spawned` | `Enemy._spawn_drops` | `source`, `position`, `item_id`, `quantity` | `LevelManager` (instantiates Pickup) |
| `score:changed` | `ScoreSystem` | `score: int`, `delta: int` | `HUD`, `SaveManager` |
| `level:exit` | `Trigger` | `trigger` | `LevelManager` |
| `level:complete` | `LevelManager` | `level_id: str` | `SaveManager`, `GameStateManager` |