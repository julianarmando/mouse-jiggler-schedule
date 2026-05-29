from __future__ import annotations
import webbrowser
import customtkinter as ctk

_GITHUB_URL = "https://github.com/julianarmando/mouse-jiggler-schedule"


class AboutTab(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="Mouse Jiggler Schedule",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, pady=(28, 4))

        ctk.CTkLabel(
            self,
            text="Keeps your computer awake by moving the mouse\non a configurable schedule.",
            text_color=("gray40", "gray70"),
            justify="center",
        ).grid(row=1, column=0, pady=(0, 24))

        ctk.CTkLabel(
            self, text="Author",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=2, column=0, pady=(0, 2))

        ctk.CTkLabel(
            self, text="@julianarmando",
        ).grid(row=3, column=0, pady=(0, 20))

        link = ctk.CTkLabel(
            self, text=_GITHUB_URL,
            text_color=("#0a84ff", "#409cff"),
            cursor="hand2",
        )
        link.grid(row=4, column=0)
        link.bind("<Button-1>", lambda _: webbrowser.open(_GITHUB_URL))
