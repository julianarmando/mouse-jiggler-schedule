# MouseJiggler - Project Context for AI-Assisted Development

## What is this project

A cross-platform (Windows + macOS) mouse jiggler desktop application built in Python.
Its primary purpose is to prevent the computer from going to sleep or showing as inactive,
with fine-grained control over how and when the mouse moves.

---

## Tech stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Cross-platform, fast dev cycle |
| UI | CustomTkinter | Modern look, native feel, easy theming |
| Mouse control | pyautogui + pynput | Cross-platform mouse movement and global hotkeys |
| System tray | pystray + Pillow | Cross-platform tray icon with menu |
| Scheduling | APScheduler | Fires schedule evaluation every 60s in background |
| Config persistence | JSON via built-in `json` | Simple, human-readable, no ORM needed |
| Packaging | PyInstaller | Generates .exe (Windows) and .app (macOS) |
| IDE | PyCharm | Primary development environment |

---

## Project structure

```
mouse_jiggler/
├── main.py                  # Entry point, wires engine + tray + app
├── app.py                   # Main window (CustomTkinter)
├── jiggler/
│   ├── __init__.py
│   ├── engine.py            # Core movement logic, background thread
│   ├── movements.py         # Movement type implementations
│   └── scheduler.py         # Schedule evaluation + APScheduler wrapper
├── ui/
│   ├── __init__.py
│   ├── tab_movement.py      # Tab: movement type + randomization options
│   ├── tab_schedule.py      # Tab: schedule editor (days + time ranges)
│   ├── tab_settings.py      # Tab: general settings (startup, tray, theme)
│   └── components.py        # Reusable widgets (LabeledSlider, StatusBar)
├── config/
│   ├── __init__.py
│   └── settings.py          # Load/save config.json, dataclasses, defaults
├── utils/
│   ├── __init__.py
│   ├── platform.py          # OS detection, startup registration, accessibility check
│   └── tray.py              # System tray icon and menu
├── assets/                  # Icon assets (generated programmatically if absent)
├── config.json              # Auto-generated user config (gitignored)
├── requirements.txt
└── CLAUDE.md                # This file
```

---

## Core features

### 1. Movement types

Two movement types, both implemented as classes inheriting `BaseMovement` in `movements.py`.

The movement API uses `get_path(amplitude, jitter) -> list[tuple[float, float]]`:
- Returns a list of `(dx, dy)` offsets from the **origin** (cursor position when jiggling started).
- The **last point must always be `(0.0, 0.0)`** so the cursor returns to its start position after each cycle.
- The engine iterates through the path with a per-step delay driven by `speed`.

| Mode | Behavior |
|---|---|
| `loop` | Smooth circular orbit. 40 steps, ~1.6s animation at speed 1.0. Traces a circle centered at `(0, amplitude/2)` with radius `amplitude/2`, starting and ending at origin. |
| `zen` | Barely visible. 10 steps with sine envelope. Drifts up to 2px (hard cap regardless of amplitude setting) and returns smoothly. |

### 2. Randomization options

Exposed as sliders in the Movement tab, stored in config:

- `amplitude` (int, 1–50px): radius of the loop orbit. Ignored by Zen (always ≤ 2px).
- `interval_base` (int, seconds): wait time between animation cycles.
- `interval_variance` (float, 0.0–1.0): random variation on the interval.
  - Actual interval = `interval_base * (1 + random(-variance, +variance))`
- `speed` (float, 0.1–2.0): controls per-step delay inside the animation.
  - `step_delay = max(0.008, 0.04 / speed)` seconds per path step.
- `jitter` (float, 0.0–1.0): additional pixel noise (currently passed to `get_path` but not yet used by Loop/Zen).

`smooth_movement` remains in the config dataclass (for future use) but has no UI control and does not affect the engine — animations are always smooth.

### 3. Schedule

Stored as a list of entries in config.json. The `ScheduleManager` uses APScheduler's `BackgroundScheduler` to fire `engine.apply_schedule()` every 60 seconds. `ScheduleEvaluator` contains the pure time-window logic.

```json
{
  "schedule": [
    {
      "enabled": true,
      "days": ["mon", "tue", "wed", "thu", "fri"],
      "start_time": "08:00",
      "end_time": "18:00",
      "label": "Work hours"
    }
  ]
}
```

The engine checks:
1. `manual_override = true` → always active, ignore schedule.
2. `schedule_enabled = false` OR `schedule` is empty → no automatic control.
3. Otherwise: activate if current time is inside any enabled entry, pause if not.

Status labels shown in the UI:
- `"Active (scheduled)"` — running due to schedule
- `"Active (manual override)"` — running due to override
- `"Active"` — running, no schedule configured
- `"Paused (outside schedule)"` — auto-paused by schedule
- `"Stopped"` — manually stopped

### 4. System tray

Always present. Icon color reflects state:
- Green = active
- Yellow = paused (outside schedule)
- Gray = stopped

Icons are generated programmatically with Pillow (colored circles, 64×64 RGBA).

Tray menu:
- Toggle Jiggler (default action)
- Show Window
- Quit

### 5. Global hotkey

Defined in config (`hotkey` field). Not yet wired to `pynput` — field exists in config but the listener is not implemented. Default value: `"ctrl+shift+j"`.

### 6. Startup with OS (no admin required)

- **Windows**: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run` via `winreg`.
- **macOS**: LaunchAgent plist at `~/Library/LaunchAgents/com.mousejiggler.plist`.

Handled in `utils/platform.py`. Toggle in Settings tab calls `platform_utils.set_startup(enabled)`.

### 7. Config persistence

Config path:
- Windows: `%APPDATA%\MouseJiggler\config.json`
- macOS: `~/Library/Application Support/MouseJiggler/config.json`

Auto-saves on every UI change. Loads on startup. Creates from defaults if missing.

---

## Config schema (current defaults)

```json
{
  "movement": {
    "mode": "loop",
    "amplitude": 10,
    "interval_base": 30,
    "interval_variance": 0.3,
    "speed": 1.0,
    "jitter": 0.0,
    "smooth_movement": true
  },
  "schedule_enabled": true,
  "manual_override": false,
  "schedule": [],
  "hotkey": "ctrl+shift+j",
  "start_with_os": false,
  "minimize_to_tray_on_close": true,
  "theme": "dark"
}
```

---

## Engine architecture

```
MainThread (UI / tkinter mainloop)
    └── JigglerEngine (daemon Thread)
            ├── ScheduleManager → APScheduler BackgroundScheduler
            │       └── fires apply_schedule() every 60s
            ├── _tick(): iterates get_path() with per-step delay
            │       └── detects user mouse movement mid-animation → aborts + resets origin
            └── _interruptible_sleep(): wakes early on pause/stop
```

Key design:
- `_running` (threading.Event): set = active, clear = paused.
- `_stop` (threading.Event): set = thread exits.
- `_origin`: cursor position at start of current jiggle session. Reset when user moves mouse > 4px from last engine position.
- `_last_engine_pos`: where the engine last placed the cursor. Used to detect user movement.
- All UI → engine calls are thread-safe (via `_lock` or atomic Event operations).
- All engine → UI callbacks go through `app.after(0, callback)` to stay on the main thread.

---

## UI layout

```
[MouseJiggler]           [Active: Scheduled]

Tabs: [ Movement ] [ Schedule ] [ Settings ]

--- Movement tab ---
Movement type:  [Loop / Zen]
Amplitude:      [slider 1-50]   10px
Interval:       [slider 5-300]  30s
Variance:       [slider 0-100]  30%
Speed:          [slider 0.1-2]  1.0x
Jitter:         [slider 0-1]    0%

--- Schedule tab ---
[ ] Enable schedule             [+ Add time window]
┌─────────────────────────────────────────┐
│ [toggle] Label      [✕]                 │
│ Days: Mon Tue Wed Thu Fri Sat Sun       │
│ From: 08:00  To: 18:00                  │
└─────────────────────────────────────────┘
[ ] Manual override (always active)

--- Settings tab ---
Start with OS:            [toggle]
Minimize to tray on close:[toggle]
Theme:                    [Dark / Light / System]

--- Controls (bottom) ---
[Start / Pause]
```

---

## Platform notes

### macOS specific
- `pyautogui` requires Accessibility permissions (System Settings → Privacy & Security → Accessibility).
- The app detects missing permissions on startup and shows a dialog.
- `pyautogui.FAILSAFE = False` is set in the engine thread (prevents corner-of-screen abort in tray-only usage).

### Windows specific
- `pyautogui.PAUSE = 0` is set in the engine thread.
- PyInstaller build: `pyinstaller --onefile --windowed --icon=assets/icon.ico main.py`

---

## Requirements

```
customtkinter>=5.2.0
pyautogui>=0.9.54
pynput>=1.7.6
pystray>=0.19.4
Pillow>=10.0.0
APScheduler>=3.10.4
pyinstaller>=6.0.0
```

On macOS, also requires: `brew install python-tk@3.13` (Tk support for the Homebrew Python).

---

## What NOT to do

- Do not use `time.sleep()` in the main thread. All waits go in the engine thread.
- Do not use tkinter directly. Only CustomTkinter widgets.
- Do not use global variables for state. State lives in the engine and config objects.
- Do not hardcode paths. Always use `pathlib.Path` and the platform config directory.
- Do not import platform-specific modules at the top level. Use lazy imports inside platform-branched functions.
- Do not move the mouse by absolute coordinates. Always use `pyautogui.moveRel`.
- Do not call UI methods directly from the engine thread. Always use `app.after(0, callback)`.
- Do not add new movement modes without implementing `get_path()` with a path that ends at `(0.0, 0.0)`.
