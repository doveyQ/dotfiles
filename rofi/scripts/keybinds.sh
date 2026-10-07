#!/usr/bin/env bash
# Keybinding cheat-sheet (Super+F1)
rofi -dmenu -i -theme ~/.config/rofi/settings.rasi -theme-str 'listview { columns: 1; lines: 14; } window { width: 560px; } entry { placeholder: "KEYBINDINGS"; }' -no-custom >/dev/null <<'KEYS'
SUPER Return          Terminal (kitty)
SUPER D  ·  SUPER R   App launcher
SUPER I               Settings hub
SUPER N               Control center
SUPER A               Dynamic island (pin open)
SUPER SHIFT X         Power menu  (p r s l e)
SUPER L               Lock (hyprlock)
SUPER CTRL N          Night mode on / off
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
SUPER 1–5             Workspaces (bottom monitor)
SUPER 6–0             Workspaces (top monitor)
SUPER SHIFT 1–0       Move window to workspace
SUPER S               Scratchpad
SUPER P  ·  SUPER J   Pseudotile · Toggle split
PRINT                 Screenshot region → clipboard
SHIFT PRINT           Screenshot → ~/Pictures
SUPER SHIFT PRINT     Record screen (red dot in island)
SUPER SHIFT R         Reload desktop
SUPER F1              This cheat-sheet
KEYS
