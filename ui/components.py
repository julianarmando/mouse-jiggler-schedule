from __future__ import annotations
import customtkinter as ctk
from typing import Callable


class LabeledSlider(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        label: str,
        from_: float,
        to: float,
        initial: float,
        format_fn: Callable[[float], str],
        on_change: Callable[[float], None],
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self._format_fn = format_fn
        self._on_change = on_change

        ctk.CTkLabel(self, text=label, width=110, anchor="w").grid(
            row=0, column=0, padx=(0, 6), sticky="w"
        )
        self._slider = ctk.CTkSlider(
            self, from_=from_, to=to, command=self._slide, width=180
        )
        self._slider.set(initial)
        self._slider.grid(row=0, column=1, padx=(0, 6))

        self._val_label = ctk.CTkLabel(self, text=format_fn(initial), width=56, anchor="w")
        self._val_label.grid(row=0, column=2, sticky="w")

    def _slide(self, value: float) -> None:
        self._val_label.configure(text=self._format_fn(value))
        self._on_change(value)

    def get(self) -> float:
        return self._slider.get()

    def set(self, value: float) -> None:
        self._slider.set(value)
        self._val_label.configure(text=self._format_fn(value))


class StatusBar(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=44, **kwargs)
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="MouseJiggler", font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=16, pady=10, sticky="w")

        self._status_label = ctk.CTkLabel(self, text="Stopped", text_color="#6b7280")
        self._status_label.grid(row=0, column=1, padx=8, pady=10)

        self._zen_label = ctk.CTkLabel(self, text="", text_color="#22c55e")
        self._zen_label.grid(row=0, column=2, padx=16, pady=10, sticky="e")

    def set_status(self, status: str) -> None:
        if "Active" in status:
            color = "#22c55e"
        elif "Paused" in status:
            color = "#eab308"
        else:
            color = "#6b7280"
        self._status_label.configure(text=status, text_color=color)

    def set_zen(self, enabled: bool) -> None:
        self._zen_label.configure(text="Zen 🍃" if enabled else "")
