
How the atlas path flows end-to-end

enemies.json
  "sprite_atlas": "content/sprites/grunt.png"
        ↓
EnemyData.sprite_atlas
        ↓
EnemyFactory.create()
    enemy.add_component(SpriteComponent(
        atlas=data.sprite_atlas,      ← stored as the dict key
        frame_width=32,
        frame_height=48,
    ))
        ↓
RenderSystem._collect_sprites()
    sprite = obj.get_component(SpriteComponent)
    DrawCall(atlas=sprite.atlas, ...)     ← same key passed to DrawCall
        ↓
RenderSystem._submit(call)
    tex = self.assets.get(call.atlas)     ← O(1) dict lookup, no I/O
    screen.blit(tex, ...)

Level hierarchy

LevelData  (data — JSON file)
└── StageData  ×  2-5
    └── WaveData  ×  2-5
        └── SpawnEntry  ×  1-8  (enemy_id, position, facing)

                    ↓ loaded and executed by

LevelManager  (manager — owns progression state)
└── StageManager  (new — owns current stage state)
    └── WaveManager / SpawnSystem  (owns current wave state)

                    ↓ all operate on

Scene  (runtime — one instance, lives forever)
└── [Player, Enemy, Platform, Pickup, Trigger, VFXObject ...]

GameSession  (new — owns player + scene + progression state)
├── player: Player                    ← persists across stages and levels
├── scene: Scene                      ← single runtime container
├── event_bus: EventBus
├── score: int
├── lives: int
│
├── LevelManager                      ← level → level progression
│   └── loads LevelData JSON
│       triggers StageManager.load_stage()
│
├── StageManager                      ← stage → stage within a level
│   └── destroys non-player objects
│       repopulates scene from StageData
│       places player at entry_position
│       triggers WaveManager.load_stage_waves()
│
└── WaveManager  (replaces SpawnSystem)
    └── watches trigger conditions
        spawns enemies per WaveData
        tracks kills via object:died
        emits wave:complete → stage:complete → level:complete

player crosses trigger zone
    → WaveManager._check_trigger() fires
        → camera:lock emitted         (camera stops scrolling)
        → enemies spawned into scene
            → player defeats all enemies
                → object:died × N
                    → WaveManager._alive empties
                        → wave:complete emitted
                            → camera:unlock emitted   (player can advance)
                            → if last wave: stage:complete emitted
                                → StageManager loads next StageData
                                    → if last stage: level:complete emitted
                                        → LevelManager loads next level
                                            → if last level: game:complete