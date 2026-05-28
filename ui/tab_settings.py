from __future__ import annotations
import customtkinter as ctk
from typing import Callable
from config.settings import Settings


class SettingsTab(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        settings: Settings,
        on_theme_change: Callable[[str], None],
        on_startup_change: Callable[[bool], None],
    ):
        super().__init__(parent, fg_color="transparent")
        self._settings = settings
        self._on_theme_change = on_theme_change
        self._on_startup_change = on_startup_change
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        config = self._settings.config
        row = 0

        # Start with OS
        r = ctk.CTkFrame(self, fg_color="transparent")
        r.grid(row=row, column=0, sticky="w", padx=16, pady=10)
        ctk.CTkLabel(r, text="Start with OS:", width=180, anchor="w").pack(side="left")
        self._startup_var = ctk.BooleanVar(value=config.start_with_os)
        ctk.CTkSwitch(
            r, text="", variable=self._startup_var,
            command=self._on_startup, width=52,
        ).pack(side="left", padx=(8, 0))
        row += 1

        # Minimize to tray on close
        r = ctk.CTkFrame(self, fg_color="transparent")
        r.grid(row=row, column=0, sticky="w", padx=16, pady=10)
        ctk.CTkLabel(r, text="Minimize to tray on close:", width=180, anchor="w").pack(side="left")
        self._tray_var = ctk.BooleanVar(value=config.minimize_to_tray_on_close)
        ctk.CTkSwitch(
            r, text="", variable=self._tray_var,
            command=self._on_tray, width=52,
        ).pack(side="left", padx=(8, 0))
        row += 1

        # Theme
        r = ctk.CTkFrame(self, fg_color="transparent")
        r.grid(row=row, column=0, sticky="w", padx=16, pady=10)
        ctk.CTkLabel(r, text="Theme:", width=180, anchor="w").pack(side="left")
        self._theme_var = ctk.StringVar(value=config.theme.capitalize())
        ctk.CTkSegmentedButton(
            r, values=["Dark", "Light", "System"],
            variable=self._theme_var,
            command=self._on_theme,
        ).pack(side="left", padx=(8, 0))
        row += 1

    def _on_startup(self) -> None:
        enabled = self._startup_var.get()
        self._settings.config.start_with_os = enabled
        self._settings.save()
        self._on_startup_change(enabled)

    def _on_tray(self) -> None:
        self._settings.config.minimize_to_tray_on_close = self._tray_var.get()
        self._settings.save()

    def _on_theme(self, value: str) -> None:
        self._settings.config.theme = value.lower()
        self._settings.save()
        self._on_theme_change(value.lower())