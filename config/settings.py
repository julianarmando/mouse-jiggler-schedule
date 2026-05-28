from __future__ import annotations
import json
import platform
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List


@dataclass
class MovementConfig:
    mode: str = "loop"
    amplitude: int = 10
    interval_base: int = 30
    interval_variance: float = 0.3
    speed: float = 1.0
    jitter: float = 0.0
    smooth_movement: bool = True


@dataclass
class ScheduleEntry:
    enabled: bool = True
    days: List[str] = field(default_factory=lambda: ["mon", "tue", "wed", "thu", "fri"])
    start_time: str = "08:00"
    end_time: str = "18:00"
    label: str = ""


@dataclass
class AppConfig:
    movement: MovementConfig = field(default_factory=MovementConfig)
    schedule_enabled: bool = True
    manual_override: bool = False
    schedule: List[ScheduleEntry] = field(default_factory=list)
    hotkey: str = "ctrl+shift+j"
    start_with_os: bool = False
    minimize_to_tray_on_close: bool = True
    theme: str = "dark"


def _get_config_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        import os
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home() / "Library" / "Application Support"
    config_dir = base / "MouseJiggler"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class Settings:
    _FILENAME = "config.json"

    def __init__(self):
        self._path = _get_config_dir() / self._FILENAME
        self.config = self._load()

    def _load(self) -> AppConfig:
        if not self._path.exists():
            cfg = AppConfig()
            self._write(cfg)
            return cfg
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            return AppConfig()

    def save(self) -> None:
        self._write(self.config)

    def _write(self, config: AppConfig) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._to_dict(config), f, indent=2)

    @staticmethod
    def _to_dict(config: AppConfig) -> dict:
        return {
            "movement": asdict(config.movement),
            "schedule_enabled": config.schedule_enabled,
            "manual_override": config.manual_override,
            "schedule": [asdict(e) for e in config.schedule],
            "hotkey": config.hotkey,
            "start_with_os": config.start_with_os,
            "minimize_to_tray_on_close": config.minimize_to_tray_on_close,
            "theme": config.theme,
        }

    @staticmethod
    def _from_dict(data: dict) -> AppConfig:
        m = data.get("movement", {})
        movement = MovementConfig(
            mode=m.get("mode", "loop"),
            amplitude=int(m.get("amplitude", 10)),
            interval_base=int(m.get("interval_base", 30)),
            interval_variance=float(m.get("interval_variance", 0.3)),
            speed=float(m.get("speed", 1.0)),
            jitter=float(m.get("jitter", 0.0)),
            smooth_movement=bool(m.get("smooth_movement", True)),
        )
        schedule = [
            ScheduleEntry(
                enabled=bool(e.get("enabled", True)),
                days=e.get("days", ["mon", "tue", "wed", "thu", "fri"]),
                start_time=e.get("start_time", "08:00"),
                end_time=e.get("end_time", "18:00"),
                label=e.get("label", ""),
            )
            for e in data.get("schedule", [])
        ]
        return AppConfig(
            movement=movement,
            schedule_enabled=bool(data.get("schedule_enabled", True)),
            manual_override=bool(data.get("manual_override", False)),
            schedule=schedule,
            hotkey=data.get("hotkey", "ctrl+shift+j"),
            start_with_os=bool(data.get("start_with_os", False)),
            minimize_to_tray_on_close=bool(data.get("minimize_to_tray_on_close", True)),
            theme=data.get("theme", "dark"),
        )
