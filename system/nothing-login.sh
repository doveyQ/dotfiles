#!/usr/bin/env bash
# Boot straight into the lock screen (greetd autologin → Hyprland started locked by
# hyprlock), or go back to the previous login manager. Must run as root:
#   sudo nothing-login.sh enable  <user>      (install.sh / Settings → Power & Lock use this)
#   sudo nothing-login.sh disable
#   nothing-login.sh status                    → "enabled" | "disabled"
# Changes take effect at the next boot — the running session is never restarted.
set -euo pipefail
HERE="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
TEMPLATE="$HERE/greetd/config.toml"
MARK=/etc/greetd/.nothing-previous-dm

current_dm() { basename "$(readlink -f /etc/systemd/system/display-manager.service 2>/dev/null)" .service; }

status() {
  if [[ "$(current_dm)" == greetd ]] && grep -q -- "--locked-cmd hyprlock" /etc/greetd/config.toml 2>/dev/null; then
    echo enabled
  else
    echo disabled
  fi
}

need_root() { [[ $EUID -eq 0 ]] || { echo "run as root (sudo / pkexec)" >&2; exit 1; }; }

case "${1:-status}" in
  status) status ;;
  enable)
    need_root
    user="${2:?usage: nothing-login.sh enable <user>}"
    id "$user" >/dev/null 2>&1 || { echo "no such user: $user" >&2; exit 1; }
    pacman -S --needed --noconfirm greetd greetd-tuigreet
    prev=$(current_dm)
    [[ -f /etc/greetd/config.toml && ! -f /etc/greetd/config.toml.orig && ! -f $MARK ]] &&
      cp /etc/greetd/config.toml /etc/greetd/config.toml.orig
    sed "s/@USER@/$user/" "$TEMPLATE" > /etc/greetd/config.toml.new
    mv /etc/greetd/config.toml.new /etc/greetd/config.toml
    install -d -o greeter -g greeter /var/cache/tuigreet     # tuigreet --remember
    if [[ -n $prev && $prev != greetd ]]; then
      echo "$prev" > "$MARK"
      systemctl disable "$prev"
    fi
    systemctl enable greetd                                   # no --now: would end the session
    echo "enabled — from the next boot (previous: ${prev:-none})"
    ;;
  disable)
    need_root
    prev=$(cat "$MARK" 2>/dev/null || true)
    if [[ -z $prev ]]; then                                    # pick an installed display manager
      for dm in sddm plasmalogin gdm lightdm ly; do
        systemctl list-unit-files "$dm.service" >/dev/null 2>&1 && { prev=$dm; break; }
      done
    fi
    [[ -n $prev ]] || { echo "no other display manager installed" >&2; exit 1; }
    systemctl disable greetd 2>/dev/null || true
    systemctl enable "$prev"
    [[ -f /etc/greetd/config.toml.orig ]] && mv /etc/greetd/config.toml.orig /etc/greetd/config.toml
    rm -f "$MARK"
    echo "disabled — $prev is the login screen from the next boot"
    ;;
  *) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
