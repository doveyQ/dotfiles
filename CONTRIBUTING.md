# Contributing

Thanks for wanting to improve this setup! Issues and pull requests are welcome.

## Workflow

1. Fork and create a branch: `git switch -c feat/short-description`
2. Make your change, then run **`make check`** — it must pass (CI runs the same script).
3. If it's visible, test it live: `make reload` (or `nothing-shell quit; nothing-shell`).
4. Add a line under **[Unreleased]** in `CHANGELOG.md`.
5. Open a PR and fill in the template (screenshots for visual changes, please).

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/):

```
feat(island): show track progress as dots
fix(hyprlock): use comma-terminated pango font names
docs: explain the lock pipeline
chore(ci): bump shellcheck
```

Scopes in use: `hypr`, `hyprlock`, `hypridle`, `island`, `control`, `waybar`, `swaync`,
`rofi`, `kitty`, `install`, `ci`, `docs`.

## Style

- **Shell**: `bash`, `set -euo pipefail` in entry points, quote everything, no warnings from
  `shellcheck -S warning`. Beware `grep -q` in pipelines under `pipefail` (SIGPIPE).
- **Python** (`nothing-shell`): standard library + PyGObject only, 4-space indent, never block
  the GTK main loop — slow work goes through `in_thread()`.
- **Hyprland**: Lua config; dispatchers are `hl.dsp.*` expressions. Validate with
  `Hyprland --verify-config -c hypr/hyprland.lua` (also loads `hypr/conf/*.lua`).
- **Design** (macOS): frosted glass + Apple system colours, in a light and a dark variant.
  Colours come only from the theme (`hypr/themes/mac-dark|mac-light/`, same names in both) —
  never hard-code a hex value in a component. Blue = on / active / selection, orange =
  warning, red = recording / destructive. SF Pro Text for UI, SF Pro Display for titles and
  large numerals, SF Pro Rounded for widget figures, SF Mono for code (`hypr/themes/typography.css`).
- No secrets, personal paths or machine-specific values in commits — use env vars or
  `*.local.*` files (git-ignored).
