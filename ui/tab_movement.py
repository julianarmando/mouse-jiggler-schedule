from __future__ import annotations
import customtkinter as ctk
from typing import Callable
from config.settings import Settings
from jiggler.movements import MOVEMENT_LABELS
from ui.components import LabeledSlider


class MovementTab(ctk.CTkFrame):
    def __init__(self, parent, settings: Settings, on_change: Callable[[], None]):
        super().__init__(parent, fg_color="transparent")
        self._settings = settings
        self._on_change = on_change
        self._build()

    def _build(self) -> None:
        mc = self._settings.config.movement
        self.grid_columnconfigure(0, weight=1)
        row = 0

        # Movement type
        type_row = ctk.CTkFrame(self, fg_color="transparent")
        type_row.grid(row=row, column=0, sticky="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(type_row, text="Movement type:", width=120, anchor="w").pack(side="left")
        self._mode_var = ctk.StringVar(value=MOVEMENT_LABELS.get(mc.mode, "Micro Jiggle"))
        ctk.CTkOptionMenu(
            type_row,
            values=list(MOVEMENT_LABELS.values()),
            variable=self._mode_var,
            command=self._on_mode_change,
            width=180,
        ).pack(side="left", padx=(8, 0))
        row += 1

        # Amplitude
        self._amplitude = LabeledSlider(
            self, "Amplitude", 1, 50, mc.amplitude,
            lambda v: f"{int(v)}px", self._on_amplitude_change,
        )
        self._amplitude.grid(row=row, column=0, sticky="w", padx=16, pady=4)
        row += 1

        # Interval
        self._interval = LabeledSlider(
            self, "Interval", 5, 300, mc.interval_base,
            lambda v: f"{int(v)}s", self._on_interval_change,
        )
        self._interval.grid(row=row, column=0, sticky="w", padx=16, pady=4)
        row += 1

        # Variance
        self._variance = LabeledSlider(
            self, "Variance", 0.0, 1.0, mc.interval_variance,
            lambda v: f"{int(v * 100)}%", self._on_variance_change,
        )
        self._variance.grid(row=row, column=0, sticky="w", padx=16, pady=4)
        row += 1

        # Speed
        self._speed = LabeledSlider(
            self, "Speed", 0.1, 5.0, mc.speed,
            lambda v: f"{v:.1f}x", self._on_speed_change,
        )
        self._speed.grid(row=row, column=0, sticky="w", padx=16, pady=4)
        row += 1

        # Jitter
        self._jitter = LabeledSlider(
            self, "Jitter", 0.0, 1.0, mc.jitter,
            lambda v: f"{int(v * 100)}%", self._on_jitter_change,
        )
        self._jitter.grid(row=row, column=0, sticky="w", padx=16, pady=(4, 12))

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _label_to_key(label: str) -> str:
        for k, v in MOVEMENT_LABELS.items():
            if v == label:
                return k
        return "loop"

    # ── callbacks ─────────────────────────────────────────────────────────

    def _on_mode_change(self, label: str) -> None:
        self._settings.config.movement.mode = self._label_to_key(label)
        self._settings.save()
        self._on_change()

    def _on_amplitude_change(self, v: float) -> None:
        self._settings.config.movement.amplitude = int(v)
        self._settings.save()

    def _on_interval_change(self, v: float) -> None:
        self._settings.config.movement.interval_base = int(v)
        self._settings.save()

    def _on_variance_change(self, v: float) -> None:
        self._settings.config.movement.interval_variance = round(v, 2)
        self._settings.save()

    def _on_speed_change(self, v: float) -> None:
        self._settings.config.movement.speed = round(v, 2)
        self._settings.save()

    def _on_jitter_change(self, v: float) -> None:
        self._settings.config.movement.jitter = round(v, 2)
        self._settings.save()

    def refresh(self) -> None:
        mc = self._settings.config.movement
        self._mode_var.set(MOVEMENT_LABELS.get(mc.mode, "Loop"))
        self._amplitude.set(mc.amplitude)
        self._interval.set(mc.interval_base)
        self._variance.set(mc.interval_variance)
        self._speed.set(mc.speed)
        self._jitter.set(mc.jitter)