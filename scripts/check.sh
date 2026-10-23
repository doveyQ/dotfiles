#!/usr/bin/env bash
# Lint & validate the whole repo. Used by `make check` and GitHub Actions.
# Tools that are missing are skipped with a notice (Hyprland isn't available in CI).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1

fail=0
ok()   { printf '  \e[2m·\e[0m %s\n' "$*"; }
bad()  { printf '  \e[31m✗\e[0m %s\n' "$*"; fail=1; }
skip() { printf '  \e[2m- %s (skipped: %s not installed)\e[0m\n' "$1" "$2"; }

mapfile -t SHELL_FILES < <(git ls-files '*.sh' 2>/dev/null || find . -name '*.sh' -not -path './.git/*')
mapfile -t PY_FILES    < <(git ls-files '*.py' 2>/dev/null || find . -name '*.py' -not -path './.git/*')
mapfile -t JSON_FILES  < <(git ls-files '*.json' '*.jsonc' 2>/dev/null || find . -name '*.json*' -not -path './.git/*')

echo "shell"
for f in "${SHELL_FILES[@]}"; do bash -n "$f" || bad "bash -n $f"; done
ok "bash -n: ${#SHELL_FILES[@]} files"
if command -v shellcheck >/dev/null; then
  shellcheck -S warning -x "${SHELL_FILES[@]}" && ok "shellcheck: clean" || bad "shellcheck"
else skip shellcheck shellcheck; fi

echo "python"
for f in "${PY_FILES[@]}"; do
  python3 -c 'import ast,sys; ast.parse(open(sys.argv[1]).read(), sys.argv[1])' "$f" || bad "syntax $f"
done
ok "syntax: ${#PY_FILES[@]} files"
if command -v ruff >/dev/null; then
  ruff check --select E9,F63,F7,F82,F401,F841 "${PY_FILES[@]}" && ok "ruff: clean" || bad "ruff"
else skip ruff ruff; fi

echo "json / jsonc"
for f in "${JSON_FILES[@]}"; do
  python3 - "$f" <<'PY' || bad "invalid json: $f"
import json, sys
src = open(sys.argv[1]).read()
out, i, n, in_str = [], 0, len(src), False
while i < n:                         # strip // and /* */ comments outside strings (JSONC)
    c = src[i]
    if in_str:
        out.append(c)
        if c == "\\": out.append(src[i + 1]); i += 1
        elif c == '"': in_str = False
    elif c == '"': in_str = True; out.append(c)
    elif src.startswith("//", i): i = src.find("\n", i); i = n if i < 0 else i; continue
    elif src.startswith("/*", i): i = src.index("*/", i) + 2; continue
    else: out.append(c)
    i += 1
json.loads("".join(out))
PY
done
ok "parsed: ${#JSON_FILES[@]} files"

echo "hyprland"
if command -v Hyprland >/dev/null; then
  Hyprland --verify-config -c hypr/hyprland.lua 2>&1 | grep "config ok" >/dev/null && ok "hyprland.lua: config ok" || {
    bad "hyprland.lua"; Hyprland --verify-config -c hypr/hyprland.lua 2>&1 | sed -n '/parsing result/,$p'; }
else skip "hyprland.lua" Hyprland; fi

echo "repo"
for f in hypr/scripts/*.sh hypr/scripts/*.py rofi/scripts/*.sh waybar/scripts/*.py nothing-shell/nothing-shell.py settings/nothing-settings.py system/*.sh install.sh scripts/*.sh; do
  [[ -x "$f" ]] || bad "not executable: $f"
done
ok "executable bits"
grep -rIl $'\r' --exclude-dir=.git . >/dev/null && bad "CRLF line endings found" || ok "line endings: LF"

((fail)) && { echo; echo "checks failed"; exit 1; }
echo; echo "all checks passed"
