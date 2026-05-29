from __future__ import annotations
import threading
import time
import random
import platform as _platform
from typing import Callable, Optional

from config.settings import Settings, MovementConfig
from jiggler.movements import BaseMovement, create_movement
from jiggler.scheduler import ScheduleEvaluator, ScheduleManager


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
        self._last_engine_pos: Optional[tuple[float, float]] = None
        self._current_status = Status.STOPPED
        self._paused_by_schedule = False

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
            self._last_engine_pos = None
            self._movement.reset()
            self._paused_by_schedule = False
            self._running.set()
        self._emit_status()

    def pause(self, by_schedule: bool = False) -> None:
        with self._lock:
            self._running.clear()
            self._origin = None
            self._last_engine_pos = None
            self._paused_by_schedule = by_schedule
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
            self._last_engine_pos = None

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
            self.pause(by_schedule=True)
        elif not should_run and not self._running.is_set():
            self._paused_by_schedule = True
            self._emit_status()
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
        mc = self._settings.config.movement
        try:
            cur_x, cur_y = pyautogui.position()

            if self._last_engine_pos is not None:
                lx, ly = self._last_engine_pos
                if abs(cur_x - lx) > 4 or abs(cur_y - ly) > 4:
                    self._origin = None
                    self._movement.reset()

            if self._origin is None:
                self._origin = (float(cur_x), float(cur_y))

            ox, oy = self._origin
            path = self._movement.get_path(mc.amplitude, mc.jitter)
            step_delay = max(0.008, 0.04 / mc.speed)
            last_moved_to = (ox, oy)

            for dx, dy in path:
                if self._stop.is_set() or not self._running.is_set():
                    return
                cur = pyautogui.position()
                # Abort animation if user moved the mouse
                if abs(cur[0] - last_moved_to[0]) > 6 or abs(cur[1] - last_moved_to[1]) > 6:
                    self._origin = None
                    self._last_engine_pos = None
                    return
                target_x = ox + dx
                target_y = oy + dy
                rel_x = round(target_x - cur[0])
                rel_y = round(target_y - cur[1])
                if rel_x != 0 or rel_y != 0:
                    pyautogui.moveRel(rel_x, rel_y, duration=0)
                last_moved_to = (target_x, target_y)
                time.sleep(step_delay)

            self._last_engine_pos = last_moved_to
        except Exception:
            pass

    def _interruptible_sleep(self, seconds: float) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if self._stop.is_set() or not self._running.is_set():
                return
            remaining = deadline - time.monotonic()
            self._stop.wait(timeout=min(0.5, remaining))

    def _compute_interval(self) -> float:
        mc = self._settings.config.movement
        factor = 1.0 + random.uniform(-mc.interval_variance, mc.interval_variance)
        return max(1.0, mc.interval_base * factor)

    def _emit_status(self) -> None:
        config = self._settings.config
        if not self._running.is_set():
            status = Status.PAUSED_SCHEDULE if self._paused_by_schedule else Status.STOPPED
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
