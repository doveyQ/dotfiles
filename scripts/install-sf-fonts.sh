#!/usr/bin/env bash
# Install Apple's SF fonts from the official .dmg downloads (developer.apple.com/fonts):
# SF-Pro.dmg, SF-Mono.dmg, SF-Compact.dmg … → ~/.local/share/fonts/SF-Pro/
#
#   scripts/install-sf-fonts.sh [dmg-or-dir …]     default: ~/Downloads
#
# A .dmg holds a .pkg (xar) holding a Payload (gzip/pbzx cpio) holding the .otf/.ttf files;
# 7-Zip unpacks every layer.  Needs: 7zip (`sudo pacman -S 7zip`).
set -euo pipefail

DEST="${XDG_DATA_HOME:-$HOME/.local/share}/fonts/SF-Pro"
SEVEN=$(command -v 7z || command -v 7zz || true)
[[ -n $SEVEN ]] || { echo "7-Zip is missing: sudo pacman -S 7zip" >&2; exit 1; }

mapfile -t DMGS < <(
  for src in "${@:-$HOME/Downloads}"; do
    if [[ -d $src ]]; then find "$src" -maxdepth 2 -iname 'SF-*.dmg'; else echo "$src"; fi
  done)
((${#DMGS[@]})) || { echo "no SF-*.dmg found (download them from https://developer.apple.com/fonts/)" >&2; exit 1; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir -p "$DEST"

for dmg in "${DMGS[@]}"; do
  echo "● $(basename "$dmg")"
  dir="$work/$(basename "$dmg" .dmg)"
  mkdir -p "$dir/0"
  "$SEVEN" x -y -bso0 -bsp0 -o"$dir/0" "$dmg" >/dev/null 2>&1 || true
  # peel the layers: .pkg → Payload → cpio, until the fonts appear (max 5 rounds)
  for round in 1 2 3 4 5; do
    [[ -n $(find "$dir" -type f \( -iname '*.otf' -o -iname '*.ttf' \) -print -quit) ]] && break
    while IFS= read -r f; do
      out="$dir/$round/$(basename "$f")"
      mkdir -p "$out"
      "$SEVEN" x -y -bso0 -bsp0 -o"$out" "$f" >/dev/null 2>&1 || true
    done < <(find "$dir/$((round - 1))" -type f \( -iname '*.pkg' -o -name 'Payload*' -o -iname '*.cpio' -o -iname '*.xar' \))
  done
  n=0
  while IFS= read -r f; do cp -f "$f" "$DEST/"; n=$((n + 1)); done \
    < <(find "$dir" -type f \( -iname '*.otf' -o -iname '*.ttf' \))
  echo "  $n font files → ${DEST/#$HOME/\~}"
done

fc-cache -f "$DEST"
echo
families=$(fc-list : family | tr ',' '\n')   # (no grep -q in a pipe: SIGPIPE + pipefail)
for fam in "SF Pro Text" "SF Pro Display" "SF Pro Rounded" "SF Mono"; do
  if grep -qx "$fam" <<<"$families"; then echo "  ✓ $fam"; else echo "  – $fam (not in these downloads)"; fi
done
