# main.py
import pygame
from backends.pygame_renderer import PygameRenderer
from systems.render_system import RenderSystem, AssetCache, Camera
from systems.camera_system import CameraSystem
from core.primitives import EventBus
from core.game_object import Scene

SCREEN_W, SCREEN_H = 800, 450
FIXED_DT = 1 / 60

def main():
    renderer   = PygameRenderer(SCREEN_W, SCREEN_H, "Beat-Em-Up")
    asset_cache= AssetCache(renderer)
    scene      = Scene(EventBus())
    camera     = Camera()
    render_sys = RenderSystem(renderer, asset_cache)

    # ... set up other systems, load level ...

    clock = pygame.time.Clock()
    accumulator = 0.0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        real_dt = clock.tick(144) / 1000.0
        accumulator += real_dt

        while accumulator >= FIXED_DT:
            scene.update(FIXED_DT)
            accumulator -= FIXED_DT

        alpha = accumulator / FIXED_DT
        render_sys.draw(scene, camera, alpha)

    pygame.quit()

if __name__ == "__main__":
    main()