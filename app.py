from __future__ import annotations
import customtkinter as ctk
from config.settings import Settings
from jiggler.engine import JigglerEngine
from ui.components import StatusBar
from ui.tab_movement import MovementTab
from ui.tab_schedule import ScheduleTab
from ui.tab_settings import SettingsTab
from utils.tray import TrayManager
import utils.platform as platform_utils


class MouseJigglerApp(ctk.CTk):
    def __init__(self, settings: Settings, engine: JigglerEngine, tray: TrayManager):
        super().__init__()
        self._settings = settings
        self._engine = engine
        self._tray = tray

        ctk.set_appearance_mode(settings.config.theme)
        self.title("MouseJiggler")
        self.geometry("580x500")
        self.resizable(False, False)

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(500, self._check_accessibility)

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._status_bar = StatusBar(self)
        self._status_bar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))

        tabs = ctk.CTkTabview(self, width=560, height=390)
        tabs.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 0))

        tabs.add("Movement")
        tabs.add("Schedule")
        tabs.add("Settings")

        MovementTab(
            tabs.tab("Movement"), self._settings,
            on_change=self._on_movement_change,
        ).pack(fill="both", expand=True)

        self._schedule_tab = ScheduleTab(
            tabs.tab("Schedule"), self._settings,
            on_change=self._on_schedule_change,
        )
        self._schedule_tab.pack(fill="both", expand=True)

        SettingsTab(
            tabs.tab("Settings"), self._settings,
            on_theme_change=self._on_theme_change,
            on_startup_change=self._on_startup_change,
        ).pack(fill="both", expand=True)

        # Controls row
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 12))

        self._toggle_btn = ctk.CTkButton(
            controls, text="Start", command=self._toggle, width=120,
        )
        self._toggle_btn.pack(side="left")

    # ── Accessibility check ───────────────────────────────────────────────

    def _check_accessibility(self) -> None:
        import platform
        if platform.system() != "Darwin":
            return
        if not platform_utils.check_accessibility_permissions():
            self._show_accessibility_dialog()

    def _show_accessibility_dialog(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("Accessibility Required")
        dialog.geometry("420x180")
        dialog.resizable(False, False)
        dialog.grab_set()
        ctk.CTkLabel(
            dialog,
            text=(
                "MouseJiggler needs Accessibility access to move the mouse.\n\n"
                "Go to: System Settings → Privacy & Security → Accessibility\n"
                "and enable this application."
            ),
            wraplength=380,
            justify="left",
        ).pack(padx=20, pady=(20, 12))
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy, width=80).pack(pady=(0, 16))

    # ── Engine callback (called from engine thread) ───────────────────────

    def on_status_change(self, status: str) -> None:
        self.after(0, lambda: self._apply_status(status))

    def _apply_status(self, status: str) -> None:
        self._status_bar.set_status(status)
        self._tray.update_state(status)
        self._toggle_btn.configure(text="Pause" if self._engine.is_running() else "Start")

    # ── User actions ──────────────────────────────────────────────────────

    def _toggle(self) -> None:
        self._engine.toggle()
        self._toggle_btn.configure(text="Pause" if self._engine.is_running() else "Start")
        self._status_bar.set_status(self._engine.get_status())
        self._tray.update_state(self._engine.get_status())

    def _on_movement_change(self) -> None:
        self._engine.set_mode(self._settings.config.movement.mode)

    def _on_schedule_change(self) -> None:
        self._engine.apply_schedule()

    def _on_theme_change(self, theme: str) -> None:
        ctk.set_appearance_mode(theme)

    def _on_startup_change(self, enabled: bool) -> None:
        platform_utils.set_startup(enabled)

    def _on_close(self) -> None:
        if self._settings.config.minimize_to_tray_on_close:
            self.withdraw()
        else:
            self.quit_app()

    def show(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def quit_app(self) -> None:
        self._engine.shutdown()
        self._tray.stop()
        self.destroy()
