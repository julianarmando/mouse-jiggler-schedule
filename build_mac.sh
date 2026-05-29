#!/bin/bash
set -e

source .venv/bin/activate

pyinstaller \
  --windowed \
  --icon=assets/icon.png \
  --name=MouseJigglerSchedule \
  --collect-all customtkinter \
  --collect-all pyautogui \
  --hidden-import pystray._darwin \
  --hidden-import pynput.keyboard._darwin \
  --hidden-import pynput.mouse._darwin \
  --add-data "assets/icon.png:assets" \
  main.py

cd dist && zip -r MouseJigglerSchedule-mac.zip MouseJigglerSchedule.app
echo "Done: dist/MouseJigglerSchedule-mac.zip"