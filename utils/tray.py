from __future__ import annotations
import threading
from typing import Callable, Optional
from PIL import Image, ImageDraw


_COLORS = {
    "active":  "#22c55e",
    "paused":  "#eab308",
    "stopped": "#6b7280",
}


def _make_icon(color: str, size: int = 64) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    m = 4
    draw.ellipse([m, m, size - m, size - m], fill=color)
    return img


def _state_from_status(status: str) -> str:
    if "Active" in status:
        return "active"
    if "Paused" in status:
        return "paused"
    return "stopped"


class TrayManager:
    def __init__(
        self,
        on_toggle: Callable[[], None],
        on_show: Callable[[], None],
        on_quit: Callable[[], None],
    ):
        self._on_toggle = on_toggle
        self._on_show = on_show
        self._on_quit = on_quit
        self._icon: Optional[object] = None

    def start(self) -> None:
        t = threading.Thread(target=self._run, daemon=True, name="TrayManager")
        t.start()

    def _run(self) -> None:
        import pystray
        img = _make_icon(_COLORS["stopped"])
        menu = pystray.Menu(
            pystray.MenuItem("Toggle Jiggler", self._on_toggle, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Window", self._on_show),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit),
        )
        self._icon = pystray.Icon("MouseJiggler", img, "MouseJiggler – Stopped", menu)
        self._icon.run()

    def update_state(self, status: str) -> None:
        if self._icon is None:
            return
        state = _state_from_status(status)
        self._icon.icon = _make_icon(_COLORS[state])
        self._icon.title = f"MouseJiggler – {status}"

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()
