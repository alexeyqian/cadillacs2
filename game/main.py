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