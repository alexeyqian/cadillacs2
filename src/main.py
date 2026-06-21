# main.py
import pygame

from backends.pygame_renderer import PygameRenderer
from backends.pygame_audio import PygameAudio
from systems.render_system import AssetCache
from game_session import GameSession
from factories.player_factory import PlayerFactory
from input.keyboard_input import KeyboardInput
from components.sprite_component import SpriteComponent
from core.paths import LEVELS_DIR, AUDIO_DIR

SCREEN_W, SCREEN_H = 800, 450
FIXED_DT            = 1 / 60

LEVEL_PATHS = [
    str(LEVELS_DIR / "level_01.json"),
    str(LEVELS_DIR / "level_02.json"),
]


def main() -> None:
    renderer    = PygameRenderer(SCREEN_W, SCREEN_H, "Beat-Em-Up")
    asset_cache = AssetCache(renderer)

    session = GameSession(renderer, asset_cache, LEVEL_PATHS, lives=3)

    # Wire pygame audio backend into the manager
    audio_backend = PygameAudio(sfx_dir=AUDIO_DIR)
    session.audio.set_backends(audio_backend.play_sfx, audio_backend.play_bgm)

    kb_input = KeyboardInput()
    player   = PlayerFactory.create(kb_input)
    session.asset_cache.load_atlas(player.get_component(SpriteComponent).atlas)
    session.player = player
    session.scene.spawn(player)

    session.start(level_index=0)

    clock       = pygame.time.Clock()
    accumulator = 0.0
    running     = True

    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        session.handle_events(events)

        real_dt      = min(clock.tick(144) / 1000.0, 0.05)
        accumulator += real_dt

        while accumulator >= FIXED_DT:
            session.update(FIXED_DT)
            accumulator -= FIXED_DT

        session.draw(accumulator / FIXED_DT)

    pygame.quit()


if __name__ == "__main__":
    main()
