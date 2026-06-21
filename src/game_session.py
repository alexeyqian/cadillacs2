"""
game_session.py
===============
GameSession — the single object that owns all runtime state for one playthrough.

Responsibilities:
    - Creates and holds: scene, event_bus, player, all managers, all systems
    - Passes itself into every manager so they share one source of truth
    - Exposes update(dt) and draw(alpha) so main.py stays as a thin clock loop
    - Listens for level/stage transitions to drive music changes

Lifecycle:
    session = GameSession(renderer, asset_cache, level_paths)
    session.start(level_index=0)      # load first level
    # game loop:
    session.handle_events(events)
    session.update(FIXED_DT)
    session.draw(alpha)
"""

from __future__ import annotations

from core.primitives import EventBus
from core.game_object import Scene
from core.paths import ENEMIES_DIR, ITEMS_DIR
from data.enemy_data import EnemyFactory, load_enemies
from data.item_data import load_items
from managers.level_manager import LevelManager, StageManager, WaveManager
from managers.audio_manager import AudioManager
from systems.physics_system import PhysicsSystem
from systems.render_system import RenderSystem, AssetCache, Camera
from systems.camera_system import CameraSystem


class GameSession:
    """
    Created once when a new game starts; survives all stage and level transitions.

    Managers and systems never import each other directly — they all hold a
    reference to this session and communicate through the shared event_bus.
    """

    def __init__(
        self,
        renderer,
        asset_cache,
        level_paths: list[str],
        lives: int = 3,
    ) -> None:
        # ── Load data registries (must happen before any factory use) ─
        load_enemies(str(ENEMIES_DIR / "enemies.json"))
        load_items(str(ITEMS_DIR / "items.json"))

        # ── Core runtime ──────────────────────────────────────
        self.event_bus  = EventBus()
        self.scene      = Scene(self.event_bus)
        self.asset_cache: AssetCache = asset_cache   # exposed so managers can preload

        # ── Player (set externally by PlayerFactory in Step 5) ─
        self.player = None

        # ── Progression state ─────────────────────────────────
        self.score               = 0
        self.lives               = lives
        self.current_level_index = 0
        self.current_stage_index = 0
        self._base_music_track   = ""

        # ── Systems ───────────────────────────────────────────
        self._physics_sys = PhysicsSystem()
        self._render_sys  = RenderSystem(renderer, asset_cache)
        self._camera      = Camera()
        self._camera_sys  = CameraSystem(follow_speed=6.0)

        # ── Managers ──────────────────────────────────────────
        _enemy_factory     = EnemyFactory()
        self.wave_manager  = WaveManager(self, _enemy_factory)
        self.stage_manager = StageManager(self, self.wave_manager)
        self.level_manager = LevelManager(level_paths, self)
        self._audio        = AudioManager()

        # ── Wire everything to the event bus ─────────────────
        self._camera_sys.on_attach(self.event_bus)
        self.level_manager.on_attach(self.event_bus)
        self.stage_manager.on_attach(self.event_bus)
        self.wave_manager.on_attach(self.event_bus)
        self._audio.on_attach(self.event_bus)

        self.event_bus.on("level:started",  self._on_level_started)
        self.event_bus.on("stage:started",  self._on_stage_started)
        self.event_bus.on("score:changed",  self._on_score_changed)

    # ── Public API ────────────────────────────────────────────

    def start(self, level_index: int = 0) -> None:
        """Load the level at index and begin the first stage."""
        self.current_level_index = level_index
        self.level_manager.load_level(level_index)

    def handle_events(self, events: list) -> None:
        """
        Forward raw pygame events to any input providers attached to the player.
        The KeyboardInput instance lives on player.input; it consumes KEYDOWN events
        each frame to track just-pressed actions.
        """
        if self.player and hasattr(self.player.input, "consume_events"):
            self.player.input.consume_events(events)

    def update(self, dt: float) -> None:
        """Fixed-timestep update. Called at exactly 60 Hz by the game loop."""
        self.scene.update(dt)
        self._physics_sys.update(dt, self.scene)
        self.wave_manager.update(dt)
        self._camera_sys.update(dt, self.scene, self._camera)

    def draw(self, alpha: float) -> None:
        """Render-rate draw. alpha = leftover accumulator / FIXED_DT."""
        self._render_sys.draw(self.scene, self._camera, alpha)

    # ── Event handlers ────────────────────────────────────────

    def _on_level_started(self, payload: dict) -> None:
        self._base_music_track = payload.get("music_track", "")

    def _on_stage_started(self, payload: dict) -> None:
        # Stage may override the level's music (e.g. boss arena)
        track = payload.get("music_track_override") or self._base_music_track
        if track:
            self._audio.play_bgm(track)

        # Fit the camera bounds to this stage's scroll limit
        limit_x = payload.get("scroll_limit_x", 4000.0)
        self._camera.bounds.x      = -200.0
        self._camera.bounds.y      = -400.0
        self._camera.bounds.width  = limit_x + 400.0
        self._camera.bounds.height = 2000.0

    def _on_score_changed(self, payload: dict) -> None:
        self.score = payload.get("score", self.score)
