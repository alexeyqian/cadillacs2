
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