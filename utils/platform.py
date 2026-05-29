from __future__ import annotations
import platform
import sys
from pathlib import Path


def get_os() -> str:
    return platform.system()


def check_accessibility_permissions() -> bool:
    if get_os() != "Darwin":
        return True
    try:
        import ctypes
        import ctypes.util
        lib = ctypes.cdll.LoadLibrary(ctypes.util.find_library("ApplicationServices"))
        lib.AXIsProcessTrusted.restype = ctypes.c_bool
        return lib.AXIsProcessTrusted()
    except Exception:
        return False


def set_startup(enabled: bool, app_name: str = "MouseJiggler") -> None:
    system = get_os()
    if system == "Windows":
        _startup_windows(enabled, app_name)
    elif system == "Darwin":
        _startup_macos(enabled, app_name)


def _startup_windows(enabled: bool, app_name: str) -> None:
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    exe = sys.executable
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe}"')
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass


def _startup_macos(enabled: bool, app_name: str) -> None:
    plist_path = (
        Path.home() / "Library" / "LaunchAgents" / f"com.{app_name.lower()}.plist"
    )
    if enabled:
        exe = sys.executable
        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{app_name.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_text(content)
    else:
        plist_path.unlink(missing_ok=True)