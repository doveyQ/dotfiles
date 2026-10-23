#!/usr/bin/env bash
# Keybinding cheat-sheet (Super+F1)
rofi -dmenu -i -theme ~/.config/rofi/settings.rasi -theme-str 'listview { columns: 1; lines: 14; } window { width: 560px; } entry { placeholder: "KEYBINDINGS"; }' -no-custom >/dev/null <<'KEYS'
SUPER Return          Terminal (kitty)
SUPER D  ·  SUPER R   App launcher
SUPER I               Settings
SUPER N               Control Center
SUPER A               Dynamic island (pin open)
SUPER SHIFT X         Power menu  (p r s l e)
SUPER L               Lock (hyprlock)
SUPER CTRL N          Night mode on / off
SUPER SHIFT T         Light ↔ Dark mode
SUPER Q               Close window
SUPER Space           Toggle floating
SUPER F               Fullscreen
SUPER V               Clipboard history
SUPER E  ·  SUPER B   Files · Browser
SUPER ← ↑ → ↓         Move focus
SUPER SHIFT ← ↑ → ↓   Move window
SUPER CTRL ← ↑ → ↓    Resize window
ALT Tab               Cycle windows
SUPER Tab             Previous workspace
SUPER 1–0             Workspaces 1–10
SUPER SHIFT 1–0       Move window to workspace
SUPER S               Scratchpad
SUPER P  ·  SUPER J   Pseudotile · Toggle split
PRINT                 Screenshot region → clipboard
SHIFT PRINT           Screenshot → ~/Pictures
SUPER SHIFT PRINT     Record screen (red dot in the menu bar)
3-finger swipe        Previous / next workspace
FN brightness keys    Screen brightness (laptop)
POWER key             Power menu (laptop)
SUPER SHIFT R         Reload desktop
SUPER F1              This cheat-sheet
KEYS
