from __future__ import annotations
import customtkinter as ctk
from typing import Callable
from config.settings import Settings, ScheduleEntry


_DAYS = [
    ("mon", "Mon"), ("tue", "Tue"), ("wed", "Wed"), ("thu", "Thu"),
    ("fri", "Fri"), ("sat", "Sat"), ("sun", "Sun"),
]


class ScheduleEntryRow(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        entry: ScheduleEntry,
        on_change: Callable[[], None],
        on_delete: Callable[[], None],
    ):
        super().__init__(parent, fg_color=("gray88", "gray20"), corner_radius=8)
        self._entry = entry
        self._on_change = on_change
        self._on_delete = on_delete
        self._build()

    def _build(self) -> None:
        # Row 1: enabled toggle + label + delete button
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(8, 4))

        self._enabled_var = ctk.BooleanVar(value=self._entry.enabled)
        ctk.CTkSwitch(
            top, text="", variable=self._enabled_var,
            command=self._save, width=44,
        ).pack(side="left")

        self._label_var = ctk.StringVar(value=self._entry.label)
        entry_widget = ctk.CTkEntry(
            top, textvariable=self._label_var,
            placeholder_text="Label (e.g. Work hours)", width=160,
        )
        entry_widget.pack(side="left", padx=(8, 0))
        self._label_var.trace_add("write", lambda *_: self._save())

        ctk.CTkButton(
            top, text="✕", width=28, height=28,
            command=self._on_delete,
            fg_color="#ef4444", hover_color="#dc2626",
        ).pack(side="right")

        # Row 2: day checkboxes
        days_row = ctk.CTkFrame(self, fg_color="transparent")
        days_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(days_row, text="Days:", width=40, anchor="w").pack(side="left")
        self._day_vars: dict[str, ctk.BooleanVar] = {}
        for key, lbl in _DAYS:
            var = ctk.BooleanVar(value=key in self._entry.days)
            self._day_vars[key] = var
            ctk.CTkCheckBox(
                days_row, text=lbl, variable=var, command=self._save,
                width=50, checkbox_width=16, checkbox_height=16,
            ).pack(side="left", padx=1)

        # Row 3: time range
        time_row = ctk.CTkFrame(self, fg_color="transparent")
        time_row.pack(fill="x", padx=10, pady=(2, 8))
        ctk.CTkLabel(time_row, text="From:", anchor="w").pack(side="left")
        self._start_var = ctk.StringVar(value=self._entry.start_time)
        ctk.CTkEntry(time_row, textvariable=self._start_var, width=64).pack(
            side="left", padx=(4, 0)
        )
        self._start_var.trace_add("write", lambda *_: self._save())
        ctk.CTkLabel(time_row, text="  To:", anchor="w").pack(side="left")
        self._end_var = ctk.StringVar(value=self._entry.end_time)
        ctk.CTkEntry(time_row, textvariable=self._end_var, width=64).pack(
            side="left", padx=(4, 0)
        )
        self._end_var.trace_add("write", lambda *_: self._save())

    def _save(self) -> None:
        self._entry.enabled = self._enabled_var.get()
        self._entry.label = self._label_var.get()
        self._entry.days = [k for k, v in self._day_vars.items() if v.get()]
        if _valid_time(self._start_var.get()):
            self._entry.start_time = self._start_var.get()
        if _valid_time(self._end_var.get()):
            self._entry.end_time = self._end_var.get()
        self._on_change()


def _valid_time(s: str) -> bool:
    try:
        h, m = s.split(":")
        return 0 <= int(h) <= 23 and 0 <= int(m) <= 59
    except (ValueError, AttributeError):
        return False


class ScheduleTab(ctk.CTkFrame):
    def __init__(self, parent, settings: Settings, on_change: Callable[[], None]):
        super().__init__(parent, fg_color="transparent")
        self._settings = settings
        self._on_change = on_change
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top: schedule toggle + add button
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(10, 4))
        self._enabled_var = ctk.BooleanVar(value=self._settings.config.schedule_enabled)
        ctk.CTkSwitch(
            top, text="Enable schedule",
            variable=self._enabled_var, command=self._on_enabled_change,
        ).pack(side="left")
        ctk.CTkButton(
            top, text="+ Add time window",
            command=self._add_entry, width=150,
        ).pack(side="right")

        # Scrollable list of entries
        self._list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list.grid(row=1, column=0, sticky="nsew", padx=16, pady=4)
        self._list.grid_columnconfigure(0, weight=1)

        # Bottom: manual override
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 10))
        self._override_var = ctk.BooleanVar(value=self._settings.config.manual_override)
        ctk.CTkSwitch(
            bottom, text="Manual override (always active)",
            variable=self._override_var, command=self._on_override_change,
        ).pack(side="left")

        self._rebuild_rows()

    def _rebuild_rows(self) -> None:
        for widget in self._list.winfo_children():
            widget.destroy()
        for i, entry in enumerate(self._settings.config.schedule):
            row = ScheduleEntryRow(
                self._list, entry,
                on_change=self._on_entry_change,
                on_delete=lambda idx=i: self._delete_entry(idx),
            )
            row.grid(row=i, column=0, sticky="ew", pady=4, padx=2)

    def _add_entry(self) -> None:
        self._settings.config.schedule.append(ScheduleEntry())
        self._settings.save()
        self._rebuild_rows()
        self._on_change()

    def _delete_entry(self, idx: int) -> None:
        entries = self._settings.config.schedule
        if 0 <= idx < len(entries):
            entries.pop(idx)
            self._settings.save()
            self._rebuild_rows()
            self._on_change()

    def _on_entry_change(self) -> None:
        self._settings.save()
        self._on_change()

    def _on_enabled_change(self) -> None:
        self._settings.config.schedule_enabled = self._enabled_var.get()
        self._settings.save()
        self._on_change()

    def _on_override_change(self) -> None:
        self._settings.config.manual_override = self._override_var.get()
        self._settings.save()
        self._on_change()

    def refresh(self) -> None:
        self._enabled_var.set(self._settings.config.schedule_enabled)
        self._override_var.set(self._settings.config.manual_override)
        self._rebuild_rows()
