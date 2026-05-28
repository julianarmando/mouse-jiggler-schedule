from __future__ import annotations
from datetime import datetime, time as dt_time
from typing import Callable, List, Optional
from config.settings import ScheduleEntry


class ScheduleEvaluator:
    _DAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}

    def is_active(self, entries: List[ScheduleEntry]) -> bool:
        now = datetime.now()
        today = self._DAY_MAP[now.weekday()]
        current = now.time().replace(second=0, microsecond=0)
        for entry in entries:
            if not entry.enabled:
                continue
            if today not in entry.days:
                continue
            if self._parse(entry.start_time) <= current <= self._parse(entry.end_time):
                return True
        return False

    @staticmethod
    def _parse(time_str: str) -> dt_time:
        h, m = map(int, time_str.split(":"))
        return dt_time(h, m)


class ScheduleManager:
    def __init__(self, on_tick: Callable[[], None]):
        self._on_tick = on_tick
        self._scheduler: Optional[object] = None

    def start(self) -> None:
        from apscheduler.schedulers.background import BackgroundScheduler
        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(self._on_tick, "interval", seconds=60, id="schedule_check")
        self._scheduler.start()
        self._on_tick()

    def stop(self) -> None:
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)