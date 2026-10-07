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
  `Hyprland --verify-config -c hypr/hyprland.lua`.
- **Design**: palette `#000000 · #141414 · #1e1e1e@80% · #ffffff · #8a8a8a · #d71921`.
  Red is an accent — one red element per surface, used for "live / active / danger".
  Dot-matrix fonts (Ndot 55/57) for numbers and headings, Inter for body text.
- No secrets, personal paths or machine-specific values in commits — use env vars or
  `*.local.*` files (git-ignored).
