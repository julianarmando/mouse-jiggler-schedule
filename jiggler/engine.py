from __future__ import annotations
import threading
import time
import random
import platform as _platform
from typing import Callable, Optional

from config.settings import Settings, MovementConfig
from jiggler.movements import BaseMovement, create_movement
from jiggler.scheduler import ScheduleEvaluator, ScheduleManager


_ZEN_CONFIG = MovementConfig(
    mode="micro_jiggle",
    amplitude=2,
    interval_base=60,
    interval_variance=0.8,
    speed=1.0,
    jitter=0.0,
    smooth_movement=True,
)


class Status:
    ACTIVE_SCHEDULED = "Active (scheduled)"
    ACTIVE_OVERRIDE = "Active (manual override)"
    ACTIVE = "Active"
    PAUSED_SCHEDULE = "Paused (outside schedule)"
    STOPPED = "Stopped"


class JigglerEngine(threading.Thread):
    def __init__(
        self,
        settings: Settings,
        on_status_change: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(daemon=True, name="JigglerEngine")
        self._settings = settings
        self.on_status_change = on_status_change
        self._running = threading.Event()
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._evaluator = ScheduleEvaluator()
        self._schedule_manager = ScheduleManager(on_tick=self.apply_schedule)
        self._movement: BaseMovement = create_movement(settings.config.movement.mode)
        self._origin: Optional[tuple[float, float]] = None
        self._zen = False
        self._current_status = Status.STOPPED

    # ── Thread lifecycle ──────────────────────────────────────────────────

    def run(self) -> None:
        self._init_pyautogui()
        self._schedule_manager.start()
        while not self._stop.is_set():
            if not self._running.is_set():
                self._stop.wait(timeout=0.2)
                continue
            self._tick()
            self._interruptible_sleep(self._compute_interval())
        self._schedule_manager.stop()

    def shutdown(self) -> None:
        self._stop.set()
        self._running.set()

    # ── Public API ────────────────────────────────────────────────────────

    def resume(self) -> None:
        with self._lock:
            self._origin = None
            self._movement.reset()
            self._running.set()
        self._emit_status()

    def pause(self) -> None:
        with self._lock:
            self._running.clear()
            self._origin = None
        self._emit_status()

    def toggle(self) -> None:
        if self._running.is_set():
            self.pause()
        else:
            self.resume()

    def is_running(self) -> bool:
        return self._running.is_set()

    def set_mode(self, mode: str) -> None:
        with self._lock:
            self._movement = create_movement(mode)
            self._origin = None

    def set_zen(self, enabled: bool) -> None:
        with self._lock:
            self._zen = enabled
            mode = "micro_jiggle" if enabled else self._settings.config.movement.mode
            self._movement = create_movement(mode)
            self._origin = None
        self._emit_status()

    def get_status(self) -> str:
        return self._current_status

    def apply_schedule(self) -> None:
        config = self._settings.config

        if config.manual_override:
            if not self._running.is_set():
                self.resume()
            else:
                self._emit_status()
            return

        if not config.schedule_enabled or not config.schedule:
            self._emit_status()
            return

        should_run = self._evaluator.is_active(config.schedule)
        if should_run and not self._running.is_set():
            self.resume()
        elif not should_run and self._running.is_set():
            self.pause()
        else:
            self._emit_status()

    # ── Internal ─────────────────────────────────────────────────────────

    def _init_pyautogui(self) -> None:
        import pyautogui
        pyautogui.FAILSAFE = False
        if _platform.system() == "Windows":
            pyautogui.PAUSE = 0

    def _tick(self) -> None:
        import pyautogui
        mc = self._effective_config()
        try:
            cur_x, cur_y = pyautogui.position()
            if self._origin is None:
                self._origin = (float(cur_x), float(cur_y))
            dx, dy = self._movement.compute_offset(mc.amplitude, mc.jitter)
            target_x = self._origin[0] + dx
            target_y = self._origin[1] + dy
            rel_x = target_x - cur_x
            rel_y = target_y - cur_y
            if mc.smooth_movement:
                self._smooth_move(rel_x, rel_y, mc.speed)
            else:
                pyautogui.moveRel(int(rel_x), int(rel_y), duration=0)
        except Exception:
            pass

    def _smooth_move(self, rel_x: float, rel_y: float, speed: float) -> None:
        import pyautogui
        steps = max(3, int(8 * speed))
        sx = rel_x / steps
        sy = rel_y / steps
        delay = max(0.003, 0.015 / speed)
        for _ in range(steps):
            if self._stop.is_set() or not self._running.is_set():
                return
            pyautogui.moveRel(sx, sy, duration=0)
            time.sleep(delay)

    def _interruptible_sleep(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if self._stop.is_set() or not self._running.is_set():
                return
            remaining = deadline - time.monotonic()
            self._stop.wait(timeout=min(0.5, remaining))

    def _compute_interval(self) -> float:
        mc = self._effective_config()
        factor = 1.0 + random.uniform(-mc.interval_variance, mc.interval_variance)
        return max(1.0, mc.interval_base * factor)

    def _effective_config(self) -> MovementConfig:
        return _ZEN_CONFIG if self._zen else self._settings.config.movement

    def _emit_status(self) -> None:
        config = self._settings.config
        if not self._running.is_set():
            status = Status.STOPPED
        elif config.manual_override:
            status = Status.ACTIVE_OVERRIDE
        elif config.schedule_enabled and config.schedule:
            status = Status.ACTIVE_SCHEDULED
        else:
            status = Status.ACTIVE
        if status != self._current_status:
            self._current_status = status
            if self.on_status_change:
                self.on_status_change(status)