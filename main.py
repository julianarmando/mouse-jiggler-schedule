from __future__ import annotations
import sys
from config.settings import Settings
from jiggler.engine import JigglerEngine
from utils.tray import TrayManager
from app import MouseJigglerApp


def main() -> None:
    settings = Settings()
    engine = JigglerEngine(settings)
    app_ref: list[MouseJigglerApp] = []

    def on_tray_toggle() -> None:
        engine.toggle()
        if app_ref:
            status = engine.get_status()
            app_ref[0].after(0, lambda: app_ref[0]._apply_status(status))

    def on_tray_zen() -> None:
        new_val = not settings.config.zen_mode
        settings.config.zen_mode = new_val
        settings.save()
        engine.set_zen(new_val)
        if app_ref:
            app_ref[0].after(0, lambda: app_ref[0]._zen_var.set(new_val))
            app_ref[0].after(0, lambda: app_ref[0]._status_bar.set_zen(new_val))

    def on_tray_show() -> None:
        if app_ref:
            app_ref[0].after(0, app_ref[0].show)

    def on_tray_quit() -> None:
        if app_ref:
            app_ref[0].after(0, app_ref[0].quit_app)
        else:
            sys.exit(0)

    tray = TrayManager(
        on_toggle=on_tray_toggle,
        on_zen_toggle=on_tray_zen,
        on_show=on_tray_show,
        on_quit=on_tray_quit,
    )

    app = MouseJigglerApp(settings, engine, tray)
    app_ref.append(app)
    engine.on_status_change = app.on_status_change

    tray.start()
    engine.start()

    app.mainloop()

    engine.shutdown()


if __name__ == "__main__":
    main()
