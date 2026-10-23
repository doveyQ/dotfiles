#!/usr/bin/env bash
# Keybinding cheat-sheet (Super+F1) — generated from the shortcuts in hypr/conf/keybinds.lua plus your
# changes (Settings → Keyboard shortcuts), so it always shows the keys that really work.
~/.local/bin/nothing-settings shortcuts |
  rofi -dmenu -i -theme ~/.config/rofi/settings.rasi \
    -theme-str 'listview { columns: 1; lines: 14; } window { width: 640px; } entry { placeholder: "KEYBINDINGS"; }' \
    -no-custom >/dev/null
