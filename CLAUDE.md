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
| Scheduling | APScheduler | Cron-like scheduling with time window support |
| Config persistence | JSON via built-in `json` | Simple, human-readable, no ORM needed |
| Packaging | PyInstaller | Generates .exe (Windows) and .app (macOS) |
| IDE | PyCharm | Primary development environment |

---

## Project structure

```
mouse_jiggler/
├── main.py                  # Entry point, initializes app and tray
├── app.py                   # Main window (CustomTkinter), wires everything together
├── jiggler/
│   ├── __init__.py
│   ├── engine.py            # Core movement logic, runs in background thread
│   ├── movements.py         # All movement type implementations
│   └── scheduler.py        # Schedule evaluation logic (time windows, days)
├── ui/
│   ├── __init__.py
│   ├── tab_movement.py      # Tab: movement type selector + randomization options
│   ├── tab_schedule.py      # Tab: schedule editor (days + time ranges)
│   ├── tab_settings.py      # Tab: general settings (hotkey, startup, tray behavior)
│   └── components.py        # Reusable UI widgets
├── config/
│   ├── __init__.py
│   └── settings.py          # Load/save config.json, defaults, validation
├── utils/
│   ├── __init__.py
│   ├── platform.py          # OS detection helpers, startup registration
│   └── tray.py              # System tray icon and menu
├── assets/
│   ├── icon.png             # App icon (used for window and tray)
│   └── icon.ico             # Windows-specific icon
├── config.json              # Auto-generated user config (gitignored)
├── requirements.txt
└── CLAUDE.md                # This file
```

---

## Core features to implement

### 1. Movement types

Each movement type is a function in `movements.py` that receives the current mouse
position and returns a new (x, y) position. The engine calls it on each tick.

| Mode | Behavior |
|---|---|
| `micro_jiggle` | Moves 1-3px in a random direction, almost invisible |
| `circular` | Orbits a fixed radius around the original position |
| `random_walk` | Soft random drift, accumulates then recenters slowly |
| `figure_eight` | Smooth figure-8 lemniscate path |
| `diagonal_bounce` | Goes diagonally, reverses on reaching amplitude limit |

All modes must use **interpolated movement** (move gradually, not teleport) when
`smooth_movement` is enabled in config.

### 2. Randomization options

Exposed as sliders/inputs in the UI, stored in config:

- `amplitude` (int, 1-50px): max distance from origin point
- `interval_base` (int, seconds): base time between movements
- `interval_variance` (float, 0.0-1.0): random variation factor on interval
  - Actual interval = `interval_base * (1 + random(-variance, +variance))`
- `speed` (float, 0.1-2.0): movement speed multiplier
- `jitter` (float, 0.0-1.0): additional pixel noise on top of the base pattern

### 3. Zen Mode

A toggle that overrides movement settings with maximum stealth values:
- Forces `micro_jiggle` mode
- Sets amplitude to 1-2px
- Sets interval to 45-90s with high variance (0.8)
- Enables smooth movement
- Disables jitter
- Shows a "Zen" indicator in the UI and tray icon

Zen mode does NOT modify the saved config. It is a runtime overlay.

### 4. Schedule

Stored as a list of schedule entries in config.json:

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

The scheduler checks every minute whether the current local time falls inside any
enabled schedule entry. If it does, the jiggler is active. If not, it pauses.

The UI shows a clear visual indicator: "Active (scheduled)" vs "Paused (outside schedule)"
vs "Active (manual override)".

Manual override: user can force-enable even outside scheduled hours via a toggle in the UI.

### 5. System tray

Always present when the app is running. Icon changes to reflect state:
- Green = active
- Yellow = paused (outside schedule)
- Gray = disabled (user manually stopped)

Tray menu:
- Toggle jiggler (Start / Pause)
- Zen Mode (checkmark)
- Show window
- Separator
- Quit

### 6. Global hotkey

Configurable in settings. Default: `Ctrl+Shift+J`.
Toggles the jiggler on/off from anywhere without opening the window.
Uses `pynput.keyboard.GlobalHotKeys`.

### 7. Startup with OS (no admin required)

- **Windows**: writes a key to `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
  using the `winreg` module. No admin needed.
- **macOS**: creates a LaunchAgent plist at `~/Library/LaunchAgents/com.mousejiggler.plist`.

Handled in `utils/platform.py` with `if platform.system() == "Windows"` branching.

### 8. Config persistence

Config is saved to:
- Windows: `%APPDATA%\MouseJiggler\config.json`
- macOS: `~/Library/Application Support/MouseJiggler/config.json`

Auto-saves on any change. Loads on startup. If missing, creates from defaults.

---

## Config schema (full default)

```json
{
  "movement": {
    "mode": "micro_jiggle",
    "amplitude": 10,
    "interval_base": 30,
    "interval_variance": 0.3,
    "speed": 1.0,
    "jitter": 0.0,
    "smooth_movement": true
  },
  "zen_mode": false,
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

The jiggler engine runs in a **background daemon thread**. It uses `threading.Event`
for pause/resume without busy-waiting.

```
MainThread (UI)
    └── JigglerEngine (Thread)
            ├── Checks schedule every tick
            ├── Calls movement function
            ├── Sleeps for interval (with variance)
            └── Fires callbacks to update UI status label
```

The UI never blocks. All state changes from UI to engine go through thread-safe
method calls on the engine instance (`engine.start()`, `engine.pause()`,
`engine.set_mode(...)`, etc.).

---

## UI layout

Single window with tabs:

```
[MouseJiggler]  [Active: Scheduled]  [Zen 🍃]

Tabs: [ Movement ] [ Schedule ] [ Settings ]

--- Movement tab ---
Movement type:  [dropdown: Micro Jiggle v]
Amplitude:      [slider 1-50]  10px
Interval:       [slider 5-300] 30s  Variance: [slider] 30%
Speed:          [slider 0.1-2] 1.0x
Jitter:         [slider 0-1]   0%
Smooth motion:  [toggle]

--- Schedule tab ---
[ ] Use schedule
[+ Add time window]
List of schedule entries (editable, deletable)
Each entry: days checkboxes + time range pickers

[ ] Manual override (ignore schedule, always active)

--- Settings tab ---
Hotkey:           [input field]
Start with OS:    [toggle]
Minimize on close:[toggle]
Theme:            [Light / Dark]
```

---

## Platform notes

### macOS specific
- `pyautogui` requires Accessibility permissions in System Settings > Privacy & Security.
- The app should detect if permissions are missing and show a clear alert with
  instructions on how to enable them.
- Do NOT use `pyautogui.FAILSAFE = True` in production (it breaks tray-only usage).

### Windows specific
- Use `pyautogui.PAUSE = 0` to disable the default 0.1s delay between calls.
- `pynput` global hotkeys work without admin on Windows.
- PyInstaller build command for single exe:
  `pyinstaller --onefile --windowed --icon=assets/icon.ico main.py`

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

---

## What NOT to do

- Do not use `time.sleep()` in the main thread. All waits go in the engine thread.
- Do not use tkinter directly. Only CustomTkinter widgets.
- Do not use global variables for state. State lives in the engine and config objects.
- Do not hardcode paths. Always use `pathlib.Path` and the platform config directory.
- Do not import platform-specific modules at the top level. Use lazy imports inside
  platform-branched functions.
- Do not move the mouse by absolute coordinates during normal operation. Always use
  relative movement (`pyautogui.moveRel`) to avoid disrupting the user's cursor position.
