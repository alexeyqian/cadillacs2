# main.py
import pygame

from backends.pygame_renderer import PygameRenderer
from systems.render_system import AssetCache
from game_session import GameSession
from core.paths import LEVELS_DIR

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

    # TODO Step 5 — PlayerFactory builds and injects the player:
    # player = PlayerFactory.create(kb_input)
    # session.player = player
    # session.scene.spawn(player)

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
