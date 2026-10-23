#!/usr/bin/env python3
"""nothing-settings — Settings app + CLI for the Nothing Hyprland desktop.

GUI
  nothing-settings [PAGE]          open the app (on PAGE)
      pages: network bluetooth sound displays appearance night notifications
             input power login keys about

CLI — every setting in the app can also be read and written here
  nothing-settings list                       all keys with their current values
  nothing-settings get KEY
  nothing-settings set KEY VALUE
  nothing-settings reset KEY|SECTION          back to the default
  nothing-settings wifi  list|scan|connect SSID [PASSWORD]|disconnect|forget SSID|on|off
  nothing-settings bt    list|scan|connect MAC|disconnect MAC|pair MAC|remove MAC|on|off
  nothing-settings dnd                        toggle Do Not Disturb
  nothing-settings install PKG…               install packages (asks for your password)

Your choices are stored in ~/.config/nothing/ (settings.json + generated settings.lua,
hypridle.conf, hyprpaper.conf) — outside the dotfiles repo, so `git status` stays clean.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

HOME = os.path.expanduser("~")
BIN = os.path.join(HOME, ".local", "bin")
APP_CSS = []   # the app's CssProvider, reloaded after a light / dark switch
HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(HERE)
CONF = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")), "nothing")
SETTINGS = os.path.join(CONF, "settings.json")
GEN_LUA = os.path.join(CONF, "settings.lua")
GEN_IDLE = os.path.join(CONF, "hypridle.conf")
GEN_PAPER = os.path.join(CONF, "hyprpaper.conf")
HYPR = os.path.join(HOME, ".config", "hypr")
WALL_DIRS = [os.path.join(HYPR, "wallpapers"), os.path.join(HOME, ".local", "share", "nothing", "wallpapers")]
LOGIN_HELPER = os.path.join(REPO, "system", "nothing-login.sh")
NIGHT = os.path.join(BIN, "nothing-night")
SHELL = os.path.join(BIN, "nothing-shell")
XKB_RULES = "/usr/share/X11/xkb/rules/evdev.lst"
PAGES = ["network", "bluetooth", "sound", "displays", "appearance", "night", "notifications",
         "input", "power", "login", "keys", "about"]
ALIASES = {"wifi": "network", "audio": "sound", "display": "displays", "monitors": "displays",
           "wallpaper": "appearance", "keyboard": "input", "mouse": "input", "touchpad": "input",
           "idle": "power", "powermode": "power", "lock": "power", "bt": "bluetooth"}


# ═══════════════════════════════ helpers ═══════════════════════════════
def run(cmd, timeout=8, input=None):
    """→ (returncode, stdout, stderr); never raises."""
    try:
        r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True,
                           timeout=timeout, input=input)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"
    except OSError as e:
        return 127, "", str(e)


def out(cmd, timeout=8):
    return run(cmd, timeout)[1]


def spawn(cmd):
    subprocess.Popen(cmd, shell=isinstance(cmd, str), start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def have(cmd):
    return shutil.which(cmd) is not None


def atomic_write(path, text):
    """Atomic, owner-only write (0600 in a 0700 dir): Hyprland executes settings.lua."""
    d = os.path.dirname(path)
    os.makedirs(d, mode=0o700, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            os.fchmod(f.fileno(), 0o600)
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def lua_str(v):
    """A Lua string literal. Backslash, quote and every control character are escaped, so no
    value (a file name, an SSID …) can end the string or break the generated file."""
    out = []
    for ch in v:
        if ch in '\\"':
            out.append("\\" + ch)
        elif ord(ch) < 0x20 or ord(ch) == 0x7f:
            out.append(f"\\{ord(ch):03d}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def lua(v, indent=0):
    """Serialise a Python value as a Lua literal."""
    pad = "    " * (indent + 1)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return lua_str(v)
    if isinstance(v, list):
        return "{\n" + "".join(f"{pad}{lua(x, indent + 1)},\n" for x in v) + "    " * indent + "}"
    if isinstance(v, dict):
        items = []
        for k, x in v.items():
            key = k if re.fullmatch(r"[A-Za-z_]\w*", k) else f"[{lua(k)}]"
            items.append(f"{pad}{key} = {lua(x, indent + 1)},\n")
        return "{\n" + "".join(items) + "    " * indent + "}"
    return "nil"


def hypr_eval(code):
    rc, o, e = run(["hyprctl", "eval", code])
    if rc != 0 or (o and o != "ok"):
        raise RuntimeError(o or e or "hyprctl eval failed")


def hypr_json(what):
    try:
        return json.loads(out(["hyprctl", "-j", *what.split()]) or "null")
    except ValueError:
        return None


def get_option(name):
    """Live Hyprland option value via `hyprctl getoption` (typed)."""
    d = hypr_json(f"getoption {name}") or {}
    for k in ("bool", "int", "float", "str"):
        if k in d:
            return d[k]
    if "css" in d:
        return int(d["css"].split()[0])
    return None


def notify(title, body="", app="Settings"):
    spawn(["notify-send", "-a", app, title, body])


def pkexec(cmd, timeout=900):
    """Run as root through polkit (hyprpolkitagent shows the password prompt)."""
    if not have("pkexec"):
        return 127, "", "pkexec not found"
    return run(["pkexec", *cmd], timeout=timeout)


def install_packages(pkgs):
    return pkexec(["pacman", "-S", "--needed", "--noconfirm", *pkgs])


# ═══════════════════════════════ settings store ═══════════════════════════════
# key → (hyprland option for live reading / lua path, type, default)
SCHEMA = {
    "keyboard.layout":             ("input:kb_layout", str, "at"),
    "keyboard.variant":            ("input:kb_variant", str, "nodeadkeys"),
    "keyboard.repeat_rate":        ("input:repeat_rate", int, 25),
    "keyboard.repeat_delay":       ("input:repeat_delay", int, 600),
    "mouse.sensitivity":           ("input:sensitivity", float, 0.0),
    "mouse.accel":                 ("input:accel_profile", str, "flat"),
    "mouse.natural_scroll":        ("input:natural_scroll", bool, False),
    "touchpad.natural_scroll":     ("input:touchpad:natural_scroll", bool, False),
    "touchpad.tap_to_click":       ("input:touchpad:tap_to_click", bool, True),
    "touchpad.disable_while_typing": ("input:touchpad:disable_while_typing", bool, True),
    "appearance.gaps_in":          ("general:gaps_in", int, 6),
    "appearance.gaps_out":         ("general:gaps_out", int, 12),
    "appearance.border":           ("general:border_size", int, 1),
    "appearance.rounding":         ("decoration:rounding", int, 14),
    "appearance.inactive_opacity": ("decoration:inactive_opacity", float, 0.96),
    "appearance.blur":             ("decoration:blur:enabled", bool, True),
    "appearance.glow":             ("decoration:glow:enabled", bool, False),
    "appearance.animations":       ("animations:enabled", bool, True),
    "appearance.wallpaper":        (None, str, os.path.join(HYPR, "theme", "wallpaper.jpg")),
    "idle.lock":                   (None, int, 15),     # minutes idle, 0 = never
    "idle.screen_off":             (None, int, 0),      # 0 here = 30 s after locking (unless set)
    "idle.suspend":                (None, int, 60),
    "idle.warn":                   (None, bool, True),
    "idle.dim":                    (None, bool, True),  # laptops: dim 30 s before locking
    "display.main":                (None, str, ""),
}
CHOICES = {
    "mouse.accel": ["flat", "adaptive"],
}


class Store:
    def __init__(self):
        try:
            with open(SETTINGS) as f:
                self.data = json.load(f)
        except (OSError, ValueError):
            self.data = {}

    def save(self):
        atomic_write(SETTINGS, json.dumps(self.data, indent=2, sort_keys=True))
        self.generate_lua()

    def has(self, key):
        sec, _, name = key.partition(".")
        return name in self.data.get(sec, {})

    def get(self, key):
        sec, _, name = key.partition(".")
        if name in self.data.get(sec, {}):
            return self.data[sec][name]
        if key == "display.main":
            return os.environ.get("NOTHING_OUTPUT", "")
        if key == "idle.screen_off":
            return "auto"                       # 30 s after locking
        opt, typ, default = SCHEMA[key]
        if opt:
            live = get_option(opt)
            if live is not None:
                return typ(live)
        return default

    def put(self, key, value):
        sec, _, name = key.partition(".")
        self.data.setdefault(sec, {})[name] = value

    def drop(self, key):
        sec, _, name = key.partition(".")
        if name:
            self.data.get(sec, {}).pop(name, None)
        else:
            self.data.pop(sec, None)

    # monitors are stored as full hl.monitor specs per output
    def monitors(self):
        return self.data.get("display", {}).get("monitors", {})

    def put_monitor(self, spec):
        self.data.setdefault("display", {}).setdefault("monitors", {})[spec["output"]] = spec

    # ── generated hyprland settings (read by hyprland.lua) ──
    def hypr_config(self):
        cfg = {}
        for key, (opt, typ, _d) in SCHEMA.items():
            if opt and self.has(key):
                node = cfg
                *path, leaf = opt.split(":")
                for p in path:
                    node = node.setdefault(p, {})
                node[leaf] = self.get(key)
        return cfg

    def generate_lua(self):
        table = {"config": self.hypr_config(), "monitors": list(self.monitors().values())}
        main = self.data.get("display", {}).get("main")
        if main:
            table["main"] = main
        atomic_write(GEN_LUA, "-- Generated by nothing-settings — change it with the Settings app or\n"
                              "-- `nothing-settings set …`. Loaded by ~/.config/hypr/hyprland.lua.\n"
                              "return " + lua(table) + "\n")


STORE = None


def store():
    global STORE
    if STORE is None:
        STORE = Store()
    return STORE


def apply_hypr(key, value):
    opt = SCHEMA[key][0]
    node = value
    for part in reversed(opt.split(":")):
        node = {part: node}
    hypr_eval("hl.config(" + lua(node).replace("\n", " ") + ")")


# ═══════════════════════════════ idle / wallpaper generation ═══════════════════════════════
def generate_idle(s):
    lock, sus = s.get("idle.lock"), s.get("idle.suspend")
    blocks = ['''# Generated by nothing-settings (Settings → Power & Lock). Defaults: ~/.config/hypr/hypridle.conf
general {
    lock_cmd = pidof hyprlock || hyprlock
    before_sleep_cmd = loginctl lock-session
    after_sleep_cmd = hyprctl dispatch 'hl.dsp.dpms({ action = "on" })'
    ignore_dbus_inhibit = false
    inhibit_sleep = 3
}
''']
    if lock > 0 and s.get("idle.warn"):
        blocks.append(f'''listener {{
    timeout = {max(30, lock * 60 - 30)}
    on-timeout = notify-send -a Idle -u low "Locking in 30 seconds" "Move the mouse to stay awake"
}}
''')
    if lock > 0 and s.get("idle.dim") and has_backlight():
        blocks.append(f'''listener {{
    timeout = {max(30, lock * 60 - 30)}
    on-timeout = brightnessctl -q -s set 10%
    on-resume = brightnessctl -q -r
}}
''')
    if lock > 0:
        blocks.append(f'''listener {{
    timeout = {lock * 60}
    on-timeout = loginctl lock-session
}}
''')
    off_s = s.get("idle.screen_off") * 60 if s.has("idle.screen_off") else (lock * 60 + 30 if lock > 0 else 0)
    if off_s > 0:
        blocks.append(f'''listener {{
    timeout = {off_s}
    on-timeout = hyprctl dispatch 'hl.dsp.dpms({{ action = "off" }})'
    on-resume = hyprctl dispatch 'hl.dsp.dpms({{ action = "on" }})'
}}
''')
    if sus > 0:
        blocks.append(f'''listener {{
    timeout = {sus * 60}
    on-timeout = systemctl suspend
}}
''')
    atomic_write(GEN_IDLE, "\n".join(blocks))


def restart_idle():
    run(["pkill", "-x", "hypridle"])
    time.sleep(0.2)
    spawn([os.path.join(HYPR, "scripts", "idle.sh")])


def generate_paper(path):
    # hyprlang: one value per line, "#" starts a comment ("##" is a literal #)
    if not os.path.isfile(path) or re.search(r"[\x00-\x1f\x7f]", path):
        raise RuntimeError("Not a usable image file")
    path = path.replace("#", "##")
    atomic_write(GEN_PAPER, f"""# Generated by nothing-settings (Settings → Appearance)
splash = false
ipc = true

wallpaper {{
    monitor =
    path = {path}
    fit_mode = cover
}}
""")


def has_backlight():
    return os.path.isdir("/sys/class/backlight") and bool(os.listdir("/sys/class/backlight"))


def brightness_get():
    m = re.search(r",(\d+)%,", out(["brightnessctl", "-m"]))
    return int(m.group(1)) if m else None


def brightness_set(pct):
    if not have("brightnessctl") or not has_backlight():
        raise RuntimeError("no adjustable backlight (laptop screens only; needs brightnessctl)")
    pct = max(1, min(100, int(float(pct))))
    run(["brightnessctl", "-q", "set", f"{pct}%"])
    return pct


def has_battery():
    try:
        return any(n.startswith("BAT") for n in os.listdir("/sys/class/power_supply"))
    except OSError:
        return False


# ═══════════════════════════════ domain backends ═══════════════════════════════
def set_setting(key, raw):
    """Validate, store, apply live. Used by both the CLI and the GUI."""
    s = store()
    if key in ("night.on", "night.temp", "night.schedule"):
        return night_set(key, raw)
    if key == "notifications.dnd":
        return dnd_set(as_bool(raw))
    if key == "power.profile":
        return power_profile_set(raw)
    if key == "login.boot_lock":
        return login_set(as_bool(raw))
    if key in ("sound.output", "sound.input"):
        return sound_default(key.split(".")[1], raw)
    if key in ("sound.volume", "sound.input_volume"):
        return sound_volume("input" if "input" in key else "output", int(float(raw)))
    if key in ("sound.mute", "sound.input_mute"):
        return sound_mute("input" if "input" in key else "output", as_bool(raw))
    if key == "display.brightness":
        return brightness_set(raw)
    if key in ("wifi.enabled", "bluetooth.enabled"):
        return (wifi_power if key.startswith("wifi") else bt_power)(as_bool(raw))
    if key.startswith("display."):
        return display_set(key, raw)
    if key not in SCHEMA:
        raise KeyError(f"unknown key: {key}  (see `nothing-settings list`)")
    if key == "idle.screen_off" and str(raw).strip() == "auto":
        reset_setting(key)
        return "auto"
    opt, typ, _ = SCHEMA[key]
    value = as_bool(raw) if typ is bool else typ(raw)
    if key in CHOICES and value not in CHOICES[key]:
        raise ValueError(f"{key} must be one of: {', '.join(CHOICES[key])}")
    if key == "keyboard.layout" and value not in xkb_layouts():
        raise ValueError(f"unknown keyboard layout: {value}")
    if key == "appearance.wallpaper":
        value = os.path.expanduser(value)
        if not os.path.isfile(value):
            raise ValueError(f"no such image: {value}")
    s.put(key, value)
    s.save()
    if opt:
        apply_hypr(key, value)
    elif key.startswith("idle."):
        generate_idle(s)
        restart_idle()
    elif key == "appearance.wallpaper":
        generate_paper(value)
        run(["hyprctl", "hyprpaper", "wallpaper", f",{value}"])
    return value


def reset_setting(key):
    s = store()
    s.drop(key)
    s.save()
    # re-apply the defaults live (a whole section, or one key)
    for k in [k for k in SCHEMA if k == key or k.startswith(key + ".")]:
        if SCHEMA[k][0]:
            apply_hypr(k, SCHEMA[k][2])
    if key.startswith("idle"):
        if not s.data.get("idle"):
            try:
                os.remove(GEN_IDLE)
            except OSError:
                pass
        else:
            generate_idle(s)
        restart_idle()
    if key in ("appearance", "appearance.wallpaper"):
        try:
            os.remove(GEN_PAPER)
        except OSError:
            pass
        run(["hyprctl", "hyprpaper", "wallpaper", f",{SCHEMA['appearance.wallpaper'][2]}"])
    if key.startswith("display"):
        run(["hyprctl", "reload"])


def as_bool(v):
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "on", "yes", "y", "enable", "enabled"):
        return True
    if s in ("0", "false", "off", "no", "n", "disable", "disabled"):
        return False
    raise ValueError(f"not a boolean: {v} (use on/off)")


# ── night ──
def night_status():
    try:
        return json.loads(out([NIGHT, "status", "--json"]) or "{}")
    except ValueError:
        return {}


def night_set(key, raw):
    if not have("hyprsunset"):
        raise RuntimeError("hyprsunset is not installed (Settings → install, or: nothing-settings install hyprsunset)")
    if key == "night.on":
        args = ["on" if as_bool(raw) else "off"]
    elif key == "night.temp":
        args = ["temp", str(int(raw))]
    else:
        raw = str(raw)
        if raw.lower() in ("off", "none", "false"):
            args = ["schedule", "off"]
        else:
            m = re.fullmatch(r"\s*(\d{1,2}:\d{2})\s*[-–>→ ]+\s*(\d{1,2}:\d{2})\s*", raw)
            if not m:
                raise ValueError("schedule must be HH:MM-HH:MM or off")
            args = ["schedule", m.group(1), m.group(2)]
    rc, o, e = run([NIGHT, *args], timeout=15)
    if rc != 0:
        raise RuntimeError(e or o or "nothing-night failed")
    return night_status()


# ── notifications ──
def dnd_get():
    return out(["swaync-client", "-D"]) == "true"


def theme_mode():
    """'dark' or 'light' — the active theme link ~/.config/hypr/theme (nothing-theme)."""
    return "light" if os.path.realpath(os.path.join(HYPR, "theme")).endswith("light") else "dark"


def theme_set(mode):
    run([os.path.join(BIN, "nothing-theme"), mode], timeout=20)


WIDGET_KINDS = (("weather", "Weather"), ("clock", "Clock"), ("calendar", "Calendar"), ("system", "System"))


def widgets_present():
    """Widget types on the desktop right now (read-only query to nothing-shell)."""
    rc, o, _e = run([os.path.join(BIN, "nothing-shell"), "widgets", "list"])
    try:
        return {w["type"] for w in json.loads(o)} if rc == 0 else set()
    except (ValueError, TypeError, KeyError):
        return set()


def widgets_cmd(*args):
    run([os.path.join(BIN, "nothing-shell"), "widgets", *args])


def dnd_set(on):
    run(["swaync-client", "-dn" if on else "-df"])
    spawn("pkill -RTMIN+9 waybar")
    return on


# ── power profile ──
def power_profiles():
    if not have("powerprofilesctl"):
        return [], None
    names = re.findall(r"^[* ]\s*([a-z-]+):\s*$", out(["powerprofilesctl", "list"]), re.M)
    return names, out(["powerprofilesctl", "get"]) or None


def power_profile_set(name):
    names, _ = power_profiles()
    if name not in names:
        raise ValueError(f"profile must be one of: {', '.join(names) or '(power-profiles-daemon not running)'}")
    rc, o, e = run(["powerprofilesctl", "set", name])
    if rc:
        raise RuntimeError(e or o)
    return name


# ── login (boot lock) ──
def login_status():
    return out([LOGIN_HELPER, "status"]) == "enabled"


def login_set(on):
    rc, o, e = pkexec([LOGIN_HELPER, "enable", os.environ.get("USER", "")] if on else [LOGIN_HELPER, "disable"])
    if rc == 126:
        raise RuntimeError("authentication cancelled")
    if rc != 0:
        raise RuntimeError(e or o or f"failed ({rc})")
    return on


# ── sound (PipeWire via pactl) ──
def sound_devices(kind):
    """kind = output|input → (list of (name, description), default_name)."""
    what = "sinks" if kind == "output" else "sources"
    try:
        devs = json.loads(out(["pactl", "--format=json", "list", what]) or "[]")
    except ValueError:
        devs = []
    items = [(d["name"], d.get("description", d["name"])) for d in devs if not d["name"].endswith(".monitor")]
    default = out(["pactl", "get-default-sink" if kind == "output" else "get-default-source"])
    return items, default


def sound_state(kind):
    target = "@DEFAULT_SINK@" if kind == "output" else "@DEFAULT_SOURCE@"
    vol = out(["pactl", "get-sink-volume" if kind == "output" else "get-source-volume", target])
    m = re.search(r"(\d+)%", vol)
    mute = "yes" in out(["pactl", "get-sink-mute" if kind == "output" else "get-source-mute", target])
    return (int(m.group(1)) if m else 0), mute


def sound_default(kind, name):
    names = [n for n, _ in sound_devices(kind)[0]]
    if name not in names:
        raise ValueError(f"no such {kind} device: {name}")
    run(["pactl", "set-default-sink" if kind == "output" else "set-default-source", name])
    return name


def sound_volume(kind, pct):
    pct = max(0, min(150, pct))
    run(["pactl", "set-sink-volume" if kind == "output" else "set-source-volume",
         "@DEFAULT_SINK@" if kind == "output" else "@DEFAULT_SOURCE@", f"{pct}%"])
    return pct


def sound_mute(kind, on):
    run(["pactl", "set-sink-mute" if kind == "output" else "set-source-mute",
         "@DEFAULT_SINK@" if kind == "output" else "@DEFAULT_SOURCE@", "1" if on else "0"])
    return on


# ── Wi-Fi (NetworkManager) ──
def _nm_split(line):
    return [p.replace("\\:", ":") for p in re.split(r"(?<!\\):", line)]


def wifi_enabled():
    return out(["nmcli", "radio", "wifi"]) == "enabled"


def wifi_power(on):
    run(["nmcli", "radio", "wifi", "on" if on else "off"])
    return on


def wifi_known():
    names = set()
    for line in out(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"]).splitlines():
        p = _nm_split(line)
        if len(p) >= 2 and p[1] == "802-11-wireless":
            names.add(p[0])
    return names


def wifi_list(rescan=False):
    raw = out(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list",
               "--rescan", "yes" if rescan else "auto"], timeout=20)
    known, nets = wifi_known(), {}
    for line in raw.splitlines():
        p = _nm_split(line)
        if len(p) < 4 or not p[1]:
            continue
        ssid, sig = p[1], int(p[2] or 0)
        cur = nets.get(ssid)
        if cur and cur["signal"] >= sig and not p[0] == "*":
            continue
        nets[ssid] = {"ssid": ssid, "signal": sig, "secure": bool(p[3] and p[3] != "--"),
                      "active": p[0] == "*" or (cur or {}).get("active", False), "known": ssid in known}
    return sorted(nets.values(), key=lambda n: (not n["active"], not n["known"], -n["signal"]))


def wifi_active():
    for line in out(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"]).splitlines():
        p = _nm_split(line)
        if len(p) >= 2 and p[1] == "802-11-wireless":
            return p[0]
    return None


def wifi_connect(ssid, password=None):
    known = ssid in wifi_known()
    previous = wifi_active()
    if known and not password:
        rc, o, e = run(["nmcli", "connection", "up", "id", ssid], timeout=45)
    else:
        # the password goes through stdin (--ask), never argv: argv is readable by every
        # local user via `ps` / /proc/<pid>/cmdline
        if password:
            rc, o, e = run(["nmcli", "--ask", "device", "wifi", "connect", ssid], timeout=45,
                           input=password + "\n")
        else:
            rc, o, e = run(["nmcli", "device", "wifi", "connect", ssid], timeout=45)
    if rc != 0:
        if not known:                       # nmcli saves a profile even when auth fails
            run(["nmcli", "connection", "delete", "id", ssid])
        if previous and previous != ssid:   # the attempt dropped the old network — get it back
            run(["nmcli", "connection", "up", "id", previous], timeout=45)
        msg = e or o or "connection failed"
        if re.search(r"[Ss]ecrets were required|802-1x|password", msg):
            msg = "Wrong password (or the network needs a username — use the connection editor)"
        raise RuntimeError(msg.replace("Error: ", "").splitlines()[-1])
    return ssid


def wifi_disconnect():
    for line in out(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device"]).splitlines():
        dev, typ, state = (_nm_split(line) + ["", "", ""])[:3]
        if typ == "wifi" and state == "connected":
            run(["nmcli", "device", "disconnect", dev])


def wifi_forget(ssid):
    rc, o, e = run(["nmcli", "connection", "delete", "id", ssid])
    if rc != 0:
        raise RuntimeError(e or o)


def ethernet_status():
    for line in out(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"]).splitlines():
        p = _nm_split(line)
        if len(p) >= 4 and p[1] == "ethernet":
            return p[0], p[2], p[3]
    return None


# ── Bluetooth (bluez) ──
def bt_service():
    return run(["systemctl", "is-active", "bluetooth"])[1] == "active"


def bt_adapter():
    return os.path.isdir("/sys/class/bluetooth") and bool(os.listdir("/sys/class/bluetooth"))


def bt_powered():
    return bt_service() and "Powered: yes" in out(["bluetoothctl", "show"], timeout=4)


def bt_power(on):
    if not bt_service():
        raise RuntimeError("the Bluetooth service is off — enable it first")
    rc, o, e = run(["bluetoothctl", "power", "on" if on else "off"], timeout=8)
    if rc != 0 or "Failed" in o:
        raise RuntimeError(o or e)
    return on


def bt_devices():
    if not bt_service():
        return []
    paired = {m for m in re.findall(r"Device ([0-9A-F:]{17})", out(["bluetoothctl", "devices", "Paired"], timeout=4))}
    devs = []
    for mac, name in re.findall(r"Device ([0-9A-F:]{17}) (.*)", out(["bluetoothctl", "devices"], timeout=4)):
        info = out(["bluetoothctl", "info", mac], timeout=4)
        icon = re.search(r"Icon: (\S+)", info)
        devs.append({"mac": mac, "name": name, "paired": mac in paired,
                     "connected": "Connected: yes" in info, "icon": icon.group(1) if icon else ""})
    return sorted(devs, key=lambda d: (not d["connected"], not d["paired"], d["name"].lower()))


def bt_scan(seconds=10):
    run(["bluetoothctl", "--timeout", str(seconds), "scan", "on"], timeout=seconds + 5)
    return bt_devices()


def bt_action(action, mac):
    if action == "pair":
        rc, o, e = run(["bluetoothctl", "--timeout", "25", "pair", mac], timeout=30)
        if rc != 0 or "Failed" in o:
            raise RuntimeError(o.splitlines()[-1] if o else e)
        run(["bluetoothctl", "trust", mac])
        action = "connect"
    rc, o, e = run(["bluetoothctl", "--timeout", "15", action, mac], timeout=20)
    if rc != 0 or "Failed" in o:
        raise RuntimeError(o.splitlines()[-1] if o else e)
    return True


# ── displays ──
def monitors():
    return hypr_json("monitors all") or []


def monitor_spec(m):
    """Current live state of a monitor as an hl.monitor() spec."""
    # no "vrr": hyprctl only says whether VRR is active right now (a "fullscreen only" monitor
    # reads false on the desktop), so VRR is only written when the user picks a value.
    return {"output": m["name"], "mode": f'{m["width"]}x{m["height"]}@{round(m["refreshRate"], 2)}',
            "position": f'{m["x"]}x{m["y"]}', "scale": round(m["scale"], 4),
            "disabled": bool(m.get("disabled"))}


def display_apply(specs):
    for spec in specs:
        hypr_eval("hl.monitor(" + lua(spec).replace("\n", " ") + ")")


def display_set(key, raw):
    """display.main OUTPUT · display.OUTPUT.(mode|scale|position|vrr|enabled) VALUE"""
    s = store()
    parts = key.split(".")
    mons = {m["name"]: m for m in monitors()}
    if parts[1] == "main":
        if raw not in mons:
            raise ValueError(f"no such output: {raw}  ({', '.join(mons)})")
        s.data.setdefault("display", {})["main"] = raw
        s.save()
        spawn([os.path.join(HYPR, "scripts", "nothing-reload.sh")])
        return raw
    if len(parts) != 3 or parts[1] not in mons:
        raise KeyError(f"use display.<{'|'.join(mons)}>.(mode|scale|position|vrr|enabled)")
    spec = s.monitors().get(parts[1]) or monitor_spec(mons[parts[1]])
    field = parts[2]
    if field == "enabled":
        spec["disabled"] = not as_bool(raw)
    elif field == "scale":
        spec["scale"] = float(raw)
    elif field == "vrr":
        spec["vrr"] = {"off": 0, "on": 1, "fullscreen": 2}.get(str(raw), None)
        if spec["vrr"] is None:
            raise ValueError("vrr must be off, on or fullscreen")
    elif field in ("mode", "position"):
        spec[field] = str(raw)
    else:
        raise KeyError(field)
    display_apply([spec])
    s.put_monitor(spec)
    s.save()
    return spec


# ── keyboard layouts ──
_xkb = None


def xkb():
    """→ (layouts {code: name}, variants {layout: [(code, name)]})"""
    global _xkb
    if _xkb:
        return _xkb
    layouts, variants, section = {}, {}, None
    try:
        with open(XKB_RULES) as f:
            for line in f:
                if line.startswith("!"):
                    section = line[1:].strip()
                    continue
                parts = line.strip().split(None, 1)
                if len(parts) < 2:
                    continue
                if section == "layout":
                    layouts[parts[0]] = parts[1]
                elif section == "variant":
                    lay, _, name = parts[1].partition(": ")
                    variants.setdefault(lay, []).append((parts[0], name))
    except OSError:
        layouts = {"us": "English (US)"}
    _xkb = (layouts, variants)
    return _xkb


def xkb_layouts():
    return xkb()[0]


# ── system info ──
def sysinfo():
    def read(p):
        try:
            return open(p).read().strip()
        except OSError:
            return ""
    osr = dict(re.findall(r'^(\w+)="?([^"\n]*)"?', read("/etc/os-release"), re.M))
    cpu = re.search(r"model name\s*:\s*(.*)", read("/proc/cpuinfo"))
    mem = re.search(r"MemTotal:\s*(\d+)", read("/proc/meminfo"))
    gpu = re.findall(r"VGA compatible controller: (.*)", out("lspci 2>/dev/null"))
    ver = out(["git", "-C", REPO, "describe", "--tags", "--always", "--dirty"])
    return [
        ("System", osr.get("PRETTY_NAME", "Linux")),
        ("Kernel", os.uname().release),
        ("Hyprland", (re.findall(r"Hyprland ([\d.]+)", out(["hyprctl", "version"])) or ["?"])[0]),
        ("Processor", cpu.group(1) if cpu else "?"),
        ("Graphics", gpu[0] if gpu else "?"),
        ("Memory", f"{int(mem.group(1)) / 1048576:.1f} GB" if mem else "?"),
        ("Host", os.uname().nodename),
        ("Dotfiles", f"{ver}  ·  {REPO}"),
    ]


# ═══════════════════════════════ CLI ═══════════════════════════════
def cli_list():
    s = store()
    rows = [(k, s.get(k)) for k in SCHEMA]
    n = night_status()
    rows += [("night.on", n.get("on")), ("night.temp", n.get("temp")),
             ("night.schedule", f'{n.get("start")}-{n.get("end")}' if n.get("schedule") else "off"),
             ("notifications.dnd", dnd_get()), ("login.boot_lock", login_status()),
             ("wifi.enabled", wifi_enabled()), ("bluetooth.enabled", bt_powered())]
    names, cur = power_profiles()
    if names:
        rows.append(("power.profile", cur))
    if has_backlight() and have("brightnessctl"):
        rows.append(("display.brightness", brightness_get()))
    for kind in ("output", "input"):
        devs, default = sound_devices(kind)
        vol, mute = sound_state(kind)
        pre = "sound." + ("" if kind == "output" else "input_")
        rows += [(f"sound.{kind}", default), (pre + "volume", vol), (pre + "mute", mute)]
    for m in monitors():
        sp = store().monitors().get(m["name"]) or monitor_spec(m)
        rows.append((f"display.{m['name']}", f'{sp["mode"]} at {sp["position"]} ×{sp["scale"]}'
                     + (" (disabled)" if sp.get("disabled") else "")))
    w = max(len(k) for k, _ in rows)
    for k, v in rows:
        mark = "*" if k in SCHEMA and s.has(k) else " "
        print(f"{mark} {k:<{w}}  {json.dumps(v) if isinstance(v, bool) else v}")
    print("\n* = changed from the default")


def cli(argv):
    cmd = argv[0]
    try:
        if cmd in ("-h", "--help", "help"):
            print(__doc__.strip())
        elif cmd == "list":
            cli_list()
        elif cmd == "get":
            key = argv[1]
            if key in SCHEMA:
                print(store().get(key))
            else:
                for line in subprocess.run([sys.argv[0], "list"], capture_output=True, text=True).stdout.splitlines():
                    if line[2:].split(" ")[0] == key:
                        print(line[2:].split(None, 1)[1].strip())
                        break
                else:
                    raise KeyError(f"unknown key: {key}")
        elif cmd == "set":
            res = set_setting(argv[1], " ".join(argv[2:]))
            print(f"{argv[1]} = {res if not isinstance(res, dict) else json.dumps(res)}")
        elif cmd == "reset":
            reset_setting(argv[1])
            print(f"{argv[1]} reset")
        elif cmd == "dnd":
            print("Do Not Disturb", "on" if dnd_set(not dnd_get()) else "off")
        elif cmd == "install":
            rc, o, e = install_packages(argv[1:])
            print(o or e)
            return rc
        elif cmd == "wifi":
            sub = argv[1] if len(argv) > 1 else "list"
            if sub in ("list", "scan"):
                for n in wifi_list(rescan=sub == "scan"):
                    print(f"{'●' if n['active'] else ' '} {n['signal']:>3}%  {'🔒' if n['secure'] else '  '} "
                          f"{n['ssid']}{'  (saved)' if n['known'] and not n['active'] else ''}")
            elif sub == "connect":
                print("connected to", wifi_connect(argv[2], argv[3] if len(argv) > 3 else None))
            elif sub == "disconnect":
                wifi_disconnect()
            elif sub == "forget":
                wifi_forget(argv[2])
            elif sub in ("on", "off"):
                wifi_power(sub == "on")
            else:
                raise KeyError(sub)
        elif cmd in ("bt", "bluetooth"):
            sub = argv[1] if len(argv) > 1 else "list"
            if sub in ("list", "scan"):
                devs = bt_scan() if sub == "scan" else bt_devices()
                for d in devs:
                    print(f"{'●' if d['connected'] else ('○' if d['paired'] else ' ')} {d['mac']}  {d['name']}")
            elif sub in ("on", "off"):
                bt_power(sub == "on")
            elif sub in ("connect", "disconnect", "pair", "remove"):
                bt_action(sub, argv[2])
            else:
                raise KeyError(sub)
        else:
            return None   # not a CLI command → GUI
        return 0
    except (KeyError, ValueError, RuntimeError, IndexError) as e:
        print("nothing-settings:", e.args[0] if e.args else e, file=sys.stderr)
        return 1


# ═══════════════════════════════ GUI ═══════════════════════════════
def gui(page):
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, Pango

    def bg(fn, done=None, err=None):
        """Run fn in a thread; deliver result / error on the GTK loop."""
        def work():
            try:
                r = fn()
                if done:
                    GLib.idle_add(lambda: (done(r), False)[1])
            except Exception as e:  # noqa: BLE001 — every failure becomes a toast
                # bind e now: Python deletes it when the except block ends
                GLib.idle_add(lambda e=e: ((err or app.win.error)(e), False)[1])
        threading.Thread(target=work, daemon=True).start()

    def lbl(text, cls=None, xalign=0.0, wrap=False, markup=False, ellipsize=False):
        w = Gtk.Label()
        (w.set_markup if markup else w.set_text)(text)
        w.set_xalign(xalign)
        if wrap:
            w.set_line_wrap(True)
            w.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            w.set_max_width_chars(60)
        if ellipsize:
            w.set_ellipsize(Pango.EllipsizeMode.END)
            w.set_max_width_chars(48)
        for c in (cls or "").split():
            w.get_style_context().add_class(c)
        return w

    def cls(w, *names):
        for n in names:
            w.get_style_context().add_class(n)
        return w

    def button(text, cb, *styles):
        b = Gtk.Button(label=text)
        cls(b, "pill", *styles)
        b.connect("clicked", lambda *_: cb())
        return b

    def switch(active, cb):
        sw = Gtk.Switch()
        sw.set_active(bool(active))
        sw.set_valign(Gtk.Align.CENTER)
        sw.connect("state-set", lambda _w, state: (cb(state), False)[1])
        return sw

    def combo(items, active, cb):
        """items: [(id, label)]"""
        c = Gtk.ComboBoxText()
        for i, t in items:
            c.append(str(i), t)
        if active is not None:
            c.set_active_id(str(active))
        c.set_valign(Gtk.Align.CENTER)
        c.connect("changed", lambda w: w.get_active_id() is not None and cb(w.get_active_id()))
        return c

    def slider(lo, hi, step, value, cb, digits=0, width=260, live=False):
        sc = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, lo, hi, step)
        sc.set_value(value)
        sc.set_digits(digits)
        sc.set_value_pos(Gtk.PositionType.RIGHT)
        sc.set_size_request(width, -1)
        sc.set_valign(Gtk.Align.CENTER)
        pending = {"t": None}

        def fire():
            pending["t"] = None
            cb(sc.get_value())
            return False

        def changed(_w):
            if pending["t"]:
                GLib.source_remove(pending["t"])
            pending["t"] = GLib.timeout_add(120 if live else 450, fire)
        sc.connect("value-changed", changed)
        return sc

    class Page(Gtk.ScrolledWindow):
        title = ""
        subtitle = ""

        def __init__(self):
            super().__init__()
            self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            cls(self.body, "page")
            self.add(self.body)
            self.built = False

        def show_page(self):
            if not self.built:
                self.built = True
                self.build()
                self.body.show_all()
            self.refresh()

        def clear(self):
            for c in self.body.get_children():
                self.body.remove(c)

        def header(self, title=None, subtitle=None):
            self.body.pack_start(lbl(title or self.title, "page-title"), False, False, 0)
            if subtitle or self.subtitle:
                self.body.pack_start(lbl(subtitle or self.subtitle, "page-sub", wrap=True), False, False, 4)

        def section(self, title):
            self.body.pack_start(lbl(title, "section", ellipsize=True), False, False, 8)
            card = Gtk.ListBox()
            card.set_selection_mode(Gtk.SelectionMode.NONE)
            cls(card, "card")
            self.body.pack_start(card, False, False, 0)
            return card

        def row(self, card, title, subtitle=None, widget=None):
            r = Gtk.ListBoxRow()
            r.set_activatable(False)
            box = Gtk.Box(spacing=16)
            cls(box, "row")
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            text.set_valign(Gtk.Align.CENTER)
            t = lbl(title, "row-title", wrap=True)
            text.pack_start(t, False, False, 0)
            sub = lbl(subtitle or "", "row-sub", wrap=True)
            sub.set_no_show_all(not subtitle)
            text.pack_start(sub, False, False, 0)
            box.pack_start(text, True, True, 0)
            if widget is not None:
                box.pack_end(widget, False, False, 0)
            r.add(box)
            card.add(r)
            r.title_label, r.sub_label = t, sub
            return r

        def need(self, card, tool, pkg, what):
            """Row offering to install a missing tool. Returns True if the tool exists."""
            if have(tool):
                return True
            self.row(card, f"{what} needs {pkg}", "Not installed yet.",
                     button("Install", lambda: app.win.install([pkg], self.rebuild), "accent"))
            return False

        def rebuild(self):
            self.clear()
            self.built = False
            self.show_page()

        def build(self):
            pass

        def refresh(self):
            pass

    # ─────────────────────────── pages ───────────────────────────
    class NetworkPage(Page):
        title, subtitle = "Network", "Wi-Fi and wired connections."

        def build(self):
            self.header()
            c = self.section("Wi-Fi")
            self.wifi_sw = switch(wifi_enabled(), lambda on: bg(lambda: wifi_power(on), lambda _r: GLib.timeout_add(1500, self._reload)))
            self.row(c, "Wi-Fi", None, self.wifi_sw)
            self.scan_btn = button("Scan", lambda: self._reload(rescan=True))
            self.row(c, "Networks nearby", "Click a network to connect.", self.scan_btn)
            self.nets = Gtk.ListBox()
            self.nets.set_selection_mode(Gtk.SelectionMode.NONE)
            cls(self.nets, "card")
            self.body.pack_start(self.nets, False, False, 0)
            e = self.section("Wired")
            self.eth_row = self.row(e, "Ethernet", "…")
            a = self.section("Advanced")
            if self.need(a, "nm-connection-editor", "network-manager-applet", "Connection editor"):
                self.row(a, "Connection editor", "VPN, static IP, proxies, hidden networks.",
                         button("Open", lambda: spawn(["nm-connection-editor"])))
            self.row(a, "Terminal UI", "nmtui in a terminal.",
                     button("Open", lambda: spawn(["kitty", "--class", "nothing-float", "-e", "nmtui"])))

        def refresh(self):
            self._reload()

        def _reload(self, rescan=False):
            self.scan_btn.set_label("Scanning…" if rescan else "Scan")
            bg(lambda: (wifi_enabled(), wifi_list(rescan), ethernet_status()), self._fill)
            return False

        def _fill(self, res):
            on, nets, eth = res
            self.scan_btn.set_label("Scan")
            self.wifi_sw.set_state(on)
            for ch in self.nets.get_children():
                self.nets.remove(ch)
            if not on:
                self.row(self.nets, "Wi-Fi is off")
            elif not nets:
                self.row(self.nets, "No networks found", "Press Scan to search again.")
            for n in nets:
                bars = "●" * max(1, round(n["signal"] / 25)) + "○" * (4 - max(1, round(n["signal"] / 25)))
                sub = ("Connected" if n["active"] else "Saved" if n["known"] else "") + \
                      (" · secured" if n["secure"] else " · open")
                actions = Gtk.Box(spacing=6)
                actions.pack_start(lbl(bars, "dots"), False, False, 6)
                if n["active"]:
                    actions.pack_start(button("Disconnect", lambda: bg(wifi_disconnect, lambda _r: self._reload())), False, False, 0)
                else:
                    actions.pack_start(button("Connect", lambda n=n: self._connect(n), "accent"), False, False, 0)
                if n["known"]:
                    actions.pack_start(button("Forget", lambda n=n: bg(lambda: wifi_forget(n["ssid"]), lambda _r: self._reload()), "danger"), False, False, 0)
                self.row(self.nets, n["ssid"], sub.strip(" ·"), actions)
            self.nets.show_all()
            if eth:
                dev, state, con = eth
                self.eth_row.sub_label.set_text(f"{dev} · {state}" + (f" · {con}" if con and con != "--" else ""))
            else:
                self.eth_row.sub_label.set_text("No wired adapter")
            self.eth_row.sub_label.show()

        def _connect(self, n):
            pw = None
            if n["secure"] and not n["known"]:
                pw = app.win.ask(f"Password for “{n['ssid']}”", password=True)
                if pw is None:
                    return
            app.win.toast(f"Connecting to {n['ssid']}…")
            bg(lambda: wifi_connect(n["ssid"], pw),
               lambda _r: (app.win.toast(f"Connected to {n['ssid']}"), self._reload()))

    class BluetoothPage(Page):
        title, subtitle = "Bluetooth", "Pair headphones, mice, keyboards and controllers."

        def build(self):
            self.header()
            c = self.section("Bluetooth")
            if not have("bluetoothctl"):
                self.need(c, "bluetoothctl", "bluez-utils", "Bluetooth")
                return
            if not bt_adapter():
                self.row(c, "No Bluetooth adapter found", "This computer has no Bluetooth hardware, or it is blocked (rfkill).")
                return
            if not bt_service():
                self.row(c, "Bluetooth service is off", "Needed for anything Bluetooth.",
                         button("Turn on service", self._enable_service, "accent"))
                return
            self.power_sw = switch(bt_powered(), lambda on: bg(lambda: bt_power(on), lambda _r: self.refresh()))
            self.row(c, "Bluetooth", None, self.power_sw)
            self.scan_btn = button("Scan", self._scan)
            self.row(c, "Devices", "Put a device into pairing mode, then Scan.", self.scan_btn)
            self.devs = Gtk.ListBox()
            self.devs.set_selection_mode(Gtk.SelectionMode.NONE)
            cls(self.devs, "card")
            self.body.pack_start(self.devs, False, False, 0)
            a = self.section("Advanced")
            if self.need(a, "blueman-manager", "blueman", "Bluetooth manager"):
                self.row(a, "Bluetooth manager", "Blueman: file transfer, audio profiles, details.",
                         button("Open", lambda: spawn(["blueman-manager"])))

        def _enable_service(self):
            app.win.toast("Enabling the Bluetooth service…")
            bg(lambda: pkexec(["systemctl", "enable", "--now", "bluetooth"]),
               lambda r: (app.win.error(RuntimeError(r[2] or "failed")) if r[0] else None, GLib.timeout_add(1200, lambda: (self.rebuild(), False)[1])))

        def refresh(self):
            if hasattr(self, "devs"):
                bg(lambda: (bt_powered(), bt_devices()), self._fill)

        def _scan(self):
            self.scan_btn.set_label("Scanning…")
            self.scan_btn.set_sensitive(False)
            bg(lambda: (bt_powered(), bt_scan()), self._fill)

        def _fill(self, res):
            powered, devs = res
            self.scan_btn.set_label("Scan")
            self.scan_btn.set_sensitive(powered)
            self.power_sw.set_state(powered)
            for ch in self.devs.get_children():
                self.devs.remove(ch)
            if not devs:
                self.row(self.devs, "No devices yet", "Turn Bluetooth on and press Scan.")
            for d in devs:
                acts = Gtk.Box(spacing=6)
                if d["connected"]:
                    acts.pack_start(button("Disconnect", lambda d=d: self._act("disconnect", d)), False, False, 0)
                elif d["paired"]:
                    acts.pack_start(button("Connect", lambda d=d: self._act("connect", d), "accent"), False, False, 0)
                else:
                    acts.pack_start(button("Pair", lambda d=d: self._act("pair", d), "accent"), False, False, 0)
                if d["paired"]:
                    acts.pack_start(button("Remove", lambda d=d: self._act("remove", d), "danger"), False, False, 0)
                state = "Connected" if d["connected"] else "Paired" if d["paired"] else "Available"
                self.row(self.devs, d["name"], f"{state} · {d['mac']}", acts)
            self.devs.show_all()

        def _act(self, action, d):
            app.win.toast(f"{action.title()}ing {d['name']}…".replace("eing", "ing"))
            bg(lambda: bt_action(action, d["mac"]), lambda _r: (app.win.toast(f"{d['name']}: done"), self.refresh()))

    class SoundPage(Page):
        title, subtitle = "Sound", "Output and input devices, volume."

        def build(self):
            self.header()
            self.widgets = {}
            for kind, name in (("output", "Output"), ("input", "Input")):
                c = self.section(name)
                devs, default = sound_devices(kind)
                dev = combo(devs, default, lambda nm, k=kind: bg(lambda: sound_default(k, nm), lambda _r: self.refresh()))
                dev.set_size_request(320, -1)
                self.row(c, "Device", None, dev)
                vol, mute = sound_state(kind)
                sc = slider(0, 150, 1, vol, lambda v, k=kind: bg(lambda: sound_volume(k, int(v))), live=True)
                self.row(c, "Volume", "Above 100 % amplifies.", sc)
                sw = switch(mute, lambda on, k=kind: bg(lambda: sound_mute(k, on)))
                self.row(c, "Mute", None, sw)
                self.widgets[kind] = (dev, sc, sw)
            a = self.section("Advanced")
            if self.need(a, "pavucontrol", "pavucontrol", "Volume mixer"):
                self.row(a, "Volume mixer", "Per-app volume, profiles, levels.",
                         button("Open", lambda: spawn(["pavucontrol"])))
            self.row(a, "Test sound", "Plays a short sound on the output.",
                     button("Play", lambda: spawn("pw-play /usr/share/sounds/freedesktop/stereo/bell.oga 2>/dev/null || paplay /usr/share/sounds/freedesktop/stereo/bell.oga")))

        def refresh(self):
            for kind, (dev, sc, sw) in self.widgets.items():
                vol, mute = sound_state(kind)
                _devs, default = sound_devices(kind)
                for w, f in ((dev, lambda: dev.set_active_id(default)), (sc, lambda: sc.set_value(vol)),
                             (sw, lambda: sw.set_state(mute))):
                    w.freeze_notify()
                    f()
                    w.thaw_notify()

    class DisplaysPage(Page):
        title, subtitle = "Displays", "Resolution, refresh rate, scale, arrangement. Changes ask for confirmation."

        def build(self):
            self.header()
            self.cards = []
            mons = monitors()
            s = store()
            main = s.data.get("display", {}).get("main") or os.environ.get("NOTHING_OUTPUT") or (mons[0]["name"] if mons else "")
            if has_backlight():
                b = self.section("Brightness")
                if self.need(b, "brightnessctl", "brightnessctl", "Brightness"):
                    self.row(b, "Built-in screen", "Also: the brightness keys.",
                             slider(1, 100, 1, brightness_get() or 50, lambda v: bg(lambda: brightness_set(v)), live=True))
            c = self.section("Main display")
            self.main_combo = combo([(m["name"], f'{m["name"]} — {m["description"][:28]}') for m in mons], main, lambda _v: None)
            self.row(c, "Island, bar, dock and notifications appear on", None, self.main_combo)
            for m in mons:
                spec = s.monitors().get(m["name"]) or monitor_spec(m)
                c = self.section(f'{m["name"]}  ·  {m["description"]}')
                en = Gtk.Switch()
                en.set_active(not spec.get("disabled"))
                en.set_valign(Gtk.Align.CENTER)
                self.row(c, "Enabled", None, en)
                modes, seen = [], set()
                for md in m.get("availableModes", []):
                    res, hz = md.split("@")
                    key = f"{res}@{float(hz.rstrip('Hz')):.2f}"
                    if key not in seen:
                        seen.add(key)
                        modes.append((key, f"{res}  ·  {float(hz.rstrip('Hz')):.0f} Hz"))
                cur_mode = f'{m["width"]}x{m["height"]}@{m["refreshRate"]:.2f}'
                if cur_mode not in seen:
                    modes.insert(0, (cur_mode, f'{m["width"]}x{m["height"]}  ·  {m["refreshRate"]:.0f} Hz'))
                mode = combo(modes, cur_mode, lambda _v: None)
                self.row(c, "Resolution & refresh rate", None, mode)
                scales = [("1.0", "100 %"), ("1.25", "125 %"), ("1.5", "150 %"), ("1.6", "160 %"), ("2.0", "200 %")]
                cur_scale = f'{float(spec["scale"]):.2f}'.rstrip("0").rstrip(".")
                cur_scale = next((k for k, _ in scales if float(k) == float(spec["scale"])), "1.0")
                scale = combo(scales, cur_scale, lambda _v: None)
                self.row(c, "Scale", None, scale)
                others = [o for o in mons if o["name"] != m["name"]]
                pos_items = [("keep", f'Keep ({spec["position"]})'), ("auto", "Automatic")]
                for o in others:
                    for rel in ("left", "right", "above", "below"):
                        pos_items.append((f"{rel}:{o['name']}", f"{rel.title()} of {o['name']}"))
                pos = combo(pos_items, "keep", lambda _v: None)
                self.row(c, "Position", None, pos)
                vrr = combo([("keep", "As configured"), ("0", "Off"), ("1", "On"), ("2", "Fullscreen only")],
                            str(spec["vrr"]) if "vrr" in spec else "keep", lambda _v: None)
                self.row(c, "Variable refresh rate", "Adaptive sync (FreeSync).", vrr)
                self.cards.append((m, en, mode, scale, pos, vrr))
            b = Gtk.Box(spacing=8)
            b.set_halign(Gtk.Align.END)
            b.pack_start(button("Reset to machine defaults", self._reset, "danger"), False, False, 0)
            b.pack_start(button("Apply", self._apply, "accent"), False, False, 0)
            self.body.pack_start(b, False, False, 12)

        def _apply(self):
            mons = {m["name"]: m for m in monitors()}
            old = [store().monitors().get(n) or monitor_spec(m) for n, m in mons.items()]
            new = []
            for m, en, mode, scale, pos, vrr in self.cards:
                spec = monitor_spec(mons[m["name"]])
                spec["disabled"] = not en.get_active()
                spec["mode"] = mode.get_active_id()
                spec["scale"] = float(scale.get_active_id())
                saved = store().monitors().get(m["name"], {})
                if vrr.get_active_id() != "keep":
                    spec["vrr"] = int(vrr.get_active_id())
                elif "vrr" in saved:
                    spec["vrr"] = saved["vrr"]
                rel = pos.get_active_id()
                if rel == "auto":
                    spec["position"] = "auto"
                elif rel != "keep":
                    side, other = rel.split(":")
                    o = mons[other]
                    ow, oh = o["width"] / o["scale"], o["height"] / o["scale"]
                    w, h = map(int, spec["mode"].split("@")[0].split("x"))
                    w, h = w / spec["scale"], h / spec["scale"]
                    x, y = {"left": (o["x"] - w, o["y"]), "right": (o["x"] + ow, o["y"]),
                            "above": (o["x"], o["y"] - h), "below": (o["x"], o["y"] + oh)}[side]
                    spec["position"] = f"{int(x)}x{int(y)}"
                new.append(spec)
            if all(s.get("disabled") for s in new):
                app.win.error(RuntimeError("At least one display must stay enabled."))
                return
            try:
                display_apply(new)
            except RuntimeError as e:
                display_apply(old)
                app.win.error(e)
                return
            main = self.main_combo.get_active_id()
            if app.win.confirm_countdown("Keep these display settings?", 15):
                s = store()
                for spec in new:
                    s.put_monitor(spec)
                if main:
                    s.data.setdefault("display", {})["main"] = main
                s.save()
                app.win.toast("Display settings saved")
                if main and main != os.environ.get("NOTHING_OUTPUT"):
                    spawn([os.path.join(HYPR, "scripts", "nothing-reload.sh")])
            else:
                display_apply(old)
                app.win.toast("Reverted")
            GLib.timeout_add(800, lambda: (self.rebuild(), False)[1])

        def _reset(self):
            reset_setting("display")
            app.win.toast("Displays reset to the machine file / automatic")
            GLib.timeout_add(1200, lambda: (self.rebuild(), False)[1])

    class AppearancePage(Page):
        title, subtitle = "Appearance", "Wallpaper, gaps, corners, blur and animation."

        def build(self):
            self.header()
            a = self.section("Appearance")
            seg = Gtk.Box(spacing=6)
            self.mode_btns = {}
            for m in ("light", "dark"):
                b = button(m.title(), lambda m=m: self._mode(m))
                seg.pack_start(b, False, False, 0)
                self.mode_btns[m] = b
            self._mark_mode(theme_mode())
            self.row(a, "Light or dark", "Menu bar, Control Center, widgets, apps and wallpaper · Super+Shift+T", seg)
            wd = self.section("Desktop widgets")
            present = widgets_present()
            for kind, name in WIDGET_KINDS:
                self.row(wd, name, None,
                         switch(kind in present, lambda on, k=kind: widgets_cmd("add" if on else "remove", k)))
            self.row(wd, "Arrange", "Drag widgets on the desktop · right-click one for size, style, remove",
                     button("Edit Widgets", lambda: widgets_cmd("edit")))
            self.row(wd, "Reset layout", "Weather, Clock, Calendar and System in their default places",
                     button("Reset", lambda: widgets_cmd("reset"), "danger"))
            c = self.section("Wallpaper")
            flow = Gtk.FlowBox()
            flow.set_max_children_per_line(4)
            flow.set_min_children_per_line(2)
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_column_spacing(10)
            flow.set_row_spacing(10)
            cls(flow, "walls")
            cur = os.path.realpath(store().get("appearance.wallpaper"))
            for d in WALL_DIRS:
                if not os.path.isdir(d):
                    continue
                for f in sorted(os.listdir(d)):
                    p = os.path.join(d, f)
                    if not f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                        continue
                    try:
                        pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(p, 200, 112, False)
                    except GLib.Error:
                        continue
                    b = Gtk.Button()
                    b.add(Gtk.Image.new_from_pixbuf(pix))
                    cls(b, "wall")
                    if os.path.realpath(p) == cur:
                        cls(b, "current")
                    b.set_tooltip_text(f)
                    b.connect("clicked", lambda _b, p=p: self._wall(p))
                    flow.add(b)
            r = Gtk.ListBoxRow()
            r.set_activatable(False)
            r.add(flow)
            c.add(r)
            self.row(c, "Add your own", "Copies the image to ~/.local/share/nothing/wallpapers.",
                     button("Choose image…", self._add))
            w = self.section("Windows")
            for key, title, lo, hi, step, digits in (
                    ("appearance.gaps_in", "Gap between windows", 0, 40, 1, 0),
                    ("appearance.gaps_out", "Gap to screen edges", 0, 60, 1, 0),
                    ("appearance.rounding", "Corner radius", 0, 40, 1, 0),
                    ("appearance.border", "Border width", 0, 6, 1, 0),
                    ("appearance.inactive_opacity", "Inactive window opacity", 0.5, 1.0, 0.01, 2)):
                self.row(w, title, None, slider(lo, hi, step, store().get(key), lambda v, k=key: self._set(k, v)))
            e = self.section("Effects")
            for key, title, sub in (("appearance.blur", "Blur", "Frosted glass behind bars, menus and see-through windows."),
                                    ("appearance.glow", "Soft glow", "A faint accent halo around the focused window."),
                                    ("appearance.animations", "Animations", None)):
                self.row(e, title, sub, switch(store().get(key), lambda on, k=key: self._set(k, on)))
            self.row(e, "Reset appearance", "Back to the Nothing defaults.", button("Reset", self._reset, "danger"))
            a = self.section("Advanced")
            if self.need(a, "nwg-look", "nwg-look", "Theme settings"):
                self.row(a, "GTK theme, icons & cursor", "nwg-look", button("Open", lambda: spawn(["nwg-look"])))

        def _set(self, key, value):
            typ = SCHEMA[key][1]
            bg(lambda: set_setting(key, typ(round(value, 2) if typ is float else value) if typ is not bool else value))

        def _mark_mode(self, mode):
            for m, b in self.mode_btns.items():
                ctx = b.get_style_context()
                (ctx.add_class if m == mode else ctx.remove_class)("accent")

        def _mode(self, mode):
            theme_set(mode)
            self._mark_mode(mode)
            Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", mode == "dark")
            for css in APP_CSS:
                css.load_from_path(os.path.join(HERE, "style.css"))

        def _wall(self, path):
            bg(lambda: set_setting("appearance.wallpaper", path), lambda _r: (app.win.toast("Wallpaper changed"), self.rebuild()))

        def _add(self):
            dlg = Gtk.FileChooserNative.new("Choose a wallpaper", app.win, Gtk.FileChooserAction.OPEN, "Use", "Cancel")
            flt = Gtk.FileFilter()
            flt.set_name("Images")
            for pat in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
                flt.add_pattern(pat)
            dlg.add_filter(flt)
            if dlg.run() == Gtk.ResponseType.ACCEPT:
                src = dlg.get_filename()
                dst_dir = WALL_DIRS[1]
                os.makedirs(dst_dir, exist_ok=True)
                dst = os.path.join(dst_dir, os.path.basename(src))
                shutil.copy2(src, dst)
                self._wall(dst)

        def _reset(self):
            reset_setting("appearance")
            app.win.toast("Appearance reset")
            self.rebuild()

    class NightPage(Page):
        title, subtitle = "Night mode", "Warmer colours in the evening — easier on the eyes and on sleep."

        def build(self):
            self.header()
            c = self.section("Night mode")
            if not self.need(c, "hyprsunset", "hyprsunset", "Night mode"):
                return
            st = night_status()
            self.on_sw = switch(st.get("on"), lambda on: self._night("night.on", "on" if on else "off"))
            self.row(c, "Night mode", "Also: Super+Ctrl+N, the NIGHT tile in the control center.", self.on_sw)
            self.temp = slider(1500, 6500, 50, st.get("temp", 4000), lambda v: self._night("night.temp", int(v)))
            self.row(c, "Warmth", "Lower = warmer. 4000 K is the default.", self.temp)
            s = self.section("Schedule")
            self.sched_sw = switch(st.get("schedule"), lambda on: self._schedule(on))
            self.row(s, "Turn on automatically", "A manual switch lasts until the next scheduled change.", self.sched_sw)
            self.start = self._time(st.get("start", "20:00"))
            self.end = self._time(st.get("end", "07:00"))
            self.row(s, "From", None, self.start[0])
            self.row(s, "Until", None, self.end[0])
            presets = Gtk.Box(spacing=6)
            for a, b, name in (("20:00", "07:00", "Evening"), ("22:00", "06:30", "Late"), ("19:00", "08:00", "Long")):
                presets.pack_start(button(name, lambda a=a, b=b: self._preset(a, b)), False, False, 0)
            self.row(s, "Presets", None, presets)

        def _time(self, hhmm):
            h, m = map(int, hhmm.split(":"))
            box = Gtk.Box(spacing=4)
            hs, ms = Gtk.SpinButton.new_with_range(0, 23, 1), Gtk.SpinButton.new_with_range(0, 59, 5)
            for sp, v in ((hs, h), (ms, m)):
                sp.set_value(v)
                sp.set_wrap(True)
                sp.connect("output", lambda s: (s.set_text(f"{int(s.get_value()):02d}"), True)[1])
                sp.connect("value-changed", lambda *_: self._times_changed())
                box.pack_start(sp, False, False, 0)
            box.pack_start(lbl(""), False, False, 0)
            return box, hs, ms

        def _hhmm(self, t):
            return f"{int(t[1].get_value()):02d}:{int(t[2].get_value()):02d}"

        def _times_changed(self):
            if getattr(self, "_debounce", None):
                GLib.source_remove(self._debounce)
            self._debounce = GLib.timeout_add(700, self._save_times)

        def _save_times(self):
            self._debounce = None
            if self.sched_sw.get_active():
                self._night("night.schedule", f"{self._hhmm(self.start)}-{self._hhmm(self.end)}")
            return False

        def _schedule(self, on):
            self._night("night.schedule", f"{self._hhmm(self.start)}-{self._hhmm(self.end)}" if on else "off")

        def _preset(self, a, b):
            for t, v in ((self.start, a), (self.end, b)):
                h, m = map(int, v.split(":"))
                t[1].set_value(h)
                t[2].set_value(m)
            self.sched_sw.set_active(True)
            self._night("night.schedule", f"{a}-{b}")

        def _night(self, key, value):
            bg(lambda: set_setting(key, value), lambda st: self._sync(st))

        def _sync(self, st):
            if isinstance(st, dict) and hasattr(self, "on_sw"):
                self.on_sw.set_state(bool(st.get("on")))

        def refresh(self):
            if hasattr(self, "on_sw"):
                st = night_status()
                self.on_sw.set_state(bool(st.get("on")))

    class NotificationsPage(Page):
        title, subtitle = "Notifications", "Popups, Do Not Disturb and history."

        def build(self):
            self.header()
            c = self.section("Notifications")
            self.dnd = switch(dnd_get(), lambda on: bg(lambda: dnd_set(on)))
            self.row(c, "Do Not Disturb", "Silences popups. Also: Super+Shift+N, right-click the bell.", self.dnd)
            self.row(c, "History", "Shown in the control center (Super+N).",
                     button("Clear history", lambda: (run([SHELL, "notif-clear"]), app.win.toast("History cleared")), "danger"))
            self.row(c, "Test", None, button("Send a test notification",
                     lambda: spawn(["notify-send", "-a", "Settings", "Hello from Nothing", "Notifications are working."])))

        def refresh(self):
            if hasattr(self, "dnd"):
                self.dnd.set_state(dnd_get())

    class InputPage(Page):
        title, subtitle = "Keyboard & mouse", "Layout, repeat, pointer speed, touchpad."

        def build(self):
            self.header()
            layouts, variants = xkb()
            c = self.section("Keyboard")
            cur = store().get("keyboard.layout")
            self.layout = combo(sorted(((k, f"{v}  ({k})") for k, v in layouts.items()), key=lambda x: x[1]), cur,
                                lambda v: self._layout(v))
            self.layout.set_size_request(320, -1)
            self.row(c, "Layout", None, self.layout)
            self.variant = Gtk.ComboBoxText()
            self.variant.set_size_request(320, -1)
            self.variant.set_valign(Gtk.Align.CENTER)
            self._fill_variants(cur, store().get("keyboard.variant"))
            self.variant.connect("changed", lambda w: w.get_active_id() is not None and bg(
                lambda: set_setting("keyboard.variant", w.get_active_id())))
            self.row(c, "Variant", "e.g. “no dead keys”: ^ ´ ` type immediately.", self.variant)
            self.row(c, "Key repeat rate", "Repeats per second.",
                     slider(10, 60, 1, store().get("keyboard.repeat_rate"), lambda v: bg(lambda: set_setting("keyboard.repeat_rate", int(v)))))
            self.row(c, "Delay before repeat", "Milliseconds.",
                     slider(150, 1000, 10, store().get("keyboard.repeat_delay"), lambda v: bg(lambda: set_setting("keyboard.repeat_delay", int(v)))))
            test = Gtk.Entry()
            test.set_placeholder_text("Type here to test…")
            test.set_size_request(320, -1)
            self.row(c, "Try it", None, test)
            m = self.section("Mouse")
            self.row(m, "Pointer speed", None, slider(-1, 1, 0.05, store().get("mouse.sensitivity"),
                     lambda v: bg(lambda: set_setting("mouse.sensitivity", round(v, 2))), digits=2))
            self.row(m, "Acceleration", "Flat = same speed always (best for gaming).",
                     combo([("flat", "Flat"), ("adaptive", "Adaptive")], store().get("mouse.accel"),
                           lambda v: bg(lambda: set_setting("mouse.accel", v))))
            self.row(m, "Natural scrolling", None, switch(store().get("mouse.natural_scroll"),
                     lambda on: bg(lambda: set_setting("mouse.natural_scroll", on))))
            devices = hypr_json("devices") or {}
            if any("touchpad" in d.get("name", "").lower() for d in devices.get("mice", [])):
                t = self.section("Touchpad")
                for key, title in (("touchpad.tap_to_click", "Tap to click"),
                                   ("touchpad.natural_scroll", "Natural scrolling"),
                                   ("touchpad.disable_while_typing", "Disable while typing")):
                    self.row(t, title, None, switch(store().get(key), lambda on, k=key: bg(lambda: set_setting(k, on))))

        def _fill_variants(self, layout, current=""):
            self._filling = True
            self.variant.remove_all()
            self.variant.append("", "Default")
            for code, name in xkb()[1].get(layout, []):
                self.variant.append(code, name)
            self.variant.set_active_id(current or "")
            self._filling = False

        def _layout(self, v):
            def work():
                set_setting("keyboard.layout", v)
                return set_setting("keyboard.variant", "")
            bg(work, lambda _r: (self._fill_variants(v, ""), app.win.toast(f"Keyboard: {xkb()[0].get(v, v)}")))

    class PowerPage(Page):
        title, subtitle = "Power & lock", "When to lock, turn off the screens and sleep."

        def build(self):
            self.header()
            s = store()
            mins = [(0, "Never"), (1, "1 minute"), (2, "2 minutes"), (5, "5 minutes"), (10, "10 minutes"),
                    (15, "15 minutes"), (20, "20 minutes"), (30, "30 minutes"), (45, "45 minutes"),
                    (60, "1 hour"), (90, "1.5 hours"), (120, "2 hours"), (180, "3 hours")]
            c = self.section("When idle")
            for key, title, sub in (("idle.lock", "Lock after", None),
                                    ("idle.screen_off", "Turn screens off after", None),
                                    ("idle.suspend", "Sleep after", "Locks first. Videos and calls keep the computer awake.")):
                cur = s.get(key)
                items = list(mins)
                if key == "idle.screen_off":
                    items.insert(0, ("auto", "30 s after locking"))
                if not any(str(m) == str(cur) for m, _ in items):
                    items.append((cur, f"{cur} minutes"))
                self.row(c, title, sub, combo(items, cur, lambda v, k=key: bg(
                    lambda: set_setting(k, v if v == "auto" else int(v)), lambda _r: app.win.toast("Saved"))))
            self.row(c, "Warn before locking", "Notification 30 seconds ahead.",
                     switch(s.get("idle.warn"), lambda on: bg(lambda: set_setting("idle.warn", on))))
            if has_backlight():
                self.row(c, "Dim before locking", None,
                         switch(s.get("idle.dim"), lambda on: bg(lambda: set_setting("idle.dim", on))))
            names, cur = power_profiles()
            if has_battery() or names:
                p = self.section("Power mode")
                if names:
                    labels = {"power-saver": "Power saver", "balanced": "Balanced", "performance": "Performance"}
                    self.row(p, "Mode", None, combo([(n, labels.get(n, n)) for n in names], cur,
                                                    lambda v: bg(lambda: set_setting("power.profile", v), lambda _r: app.win.toast(f"Power mode: {v}"))))
                else:
                    self.need(p, "powerprofilesctl", "power-profiles-daemon", "Power modes")
            k = self.section("Lock")
            self.row(k, "Lock now", "Same as Super+L.", button("Lock", lambda: spawn(["loginctl", "lock-session"])))
            self.row(k, "Lock screen at boot", "Settings → Login screen.", button("Open", lambda: app.win.go("login")))

    class LoginPage(Page):
        title, subtitle = "Login screen", ("Start the computer straight into the Nothing lock screen instead of the "
                                           "standard (SDDM / Plasma) login. You type your password on hyprlock.")

        def build(self):
            self.header()
            c = self.section("At boot")
            on = login_status()
            self.sw = switch(on, self._toggle)
            self.state = self.row(c, "Boot into the Nothing lock screen",
                                  "On — greetd starts Hyprland already locked." if on else
                                  "Off — your distribution's login screen is used.", self.sw)
            self.row(c, "Takes effect", "At the next boot. Asks for your password (administrator).")
            n = self.section("Good to know")
            self.row(n, "Wallets", "KWallet / GNOME Keyring are not unlocked automatically — apps ask once.")
            self.row(n, "Other sessions", "After logging out you get a text login; F3 picks e.g. Plasma.")
            self.row(n, "Undo", "Switch this off, or run: ~/dotfiles/install.sh --restore-login")

        def _toggle(self, on):
            app.win.toast("Waiting for your password…")
            bg(lambda: login_set(on),
               lambda _r: (app.win.toast("Done — active from the next boot"), self.rebuild()),
               lambda e: (app.win.error(e), self.rebuild()))

    class KeysPage(Page):
        title, subtitle = "Keyboard shortcuts", "Super is the Windows key."

        def build(self):
            self.header()
            path = os.path.join(REPO, "rofi", "scripts", "keybinds.sh")
            try:
                text = open(path).read()
                lines = text.split("<<'KEYS'\n", 1)[1].split("\nKEYS", 1)[0].splitlines()
            except (OSError, IndexError):
                lines = []
            c = self.section("Shortcuts")
            for line in lines:
                keys, _, what = line.partition("  ")
                self.row(c, what.strip(), None, lbl(keys.strip().replace(" ", " + ").replace("+ +", "+").replace("·", " · "), "kbd"))

    class AboutPage(Page):
        title, subtitle = "About", ""

        def build(self):
            self.header()
            c = self.section("This computer")
            for k, v in sysinfo():
                self.row(c, k, None, lbl(v, "value", xalign=1, ellipsize=True))
            d = self.section("Dotfiles")
            self.row(d, "Update", "git pull + relink (your settings in ~/.config/nothing stay).",
                     button("Update", self._update, "accent"))
            self.row(d, "Reload the desktop", "Island, bars, popups, wallpaper, idle.",
                     button("Reload", lambda: spawn([os.path.join(HYPR, "scripts", "nothing-reload.sh")])))
            self.row(d, "Machine file", "hyprland.local.lua — monitors, devices, extras for this computer.",
                     button("Edit", self._edit_local))
            self.row(d, "Open the dotfiles folder", REPO, button("Open", lambda: spawn(["xdg-open", REPO])))
            self.row(d, "Guide", "docs/GUIDE.md — everything explained.",
                     button("Read", lambda: spawn(["xdg-open", os.path.join(REPO, "docs", "GUIDE.md")])))
            self.row(d, "Reset all settings", "Removes ~/.config/nothing — back to the defaults.",
                     button("Reset all", self._reset_all, "danger"))

        def _update(self):
            app.win.toast("Updating…")

            def work():
                rc, o, e = run(["git", "-C", REPO, "pull", "--ff-only"], timeout=60)
                if rc:
                    raise RuntimeError(e or o)
                run([os.path.join(REPO, "install.sh"), "--links-only"], timeout=120)
                return o.splitlines()[-1] if o else "up to date"
            bg(work, lambda msg: (app.win.toast(msg), self.rebuild()))

        def _edit_local(self):
            p = os.path.join(HYPR, "hyprland.local.lua")
            if not os.path.exists(p):
                ex = os.path.join(HYPR, "examples", "laptop.lua" if has_battery() else "desktop-dual-monitor.lua")
                shutil.copy(ex, p)
            spawn(["kitty", "--class", "nothing-float", "-e", os.environ.get("EDITOR", "nano"), p])

        def _reset_all(self):
            if not app.win.confirm("Reset every setting to the default?"):
                return
            for p in (SETTINGS, GEN_LUA, GEN_IDLE, GEN_PAPER):
                try:
                    os.remove(p)
                except OSError:
                    pass
            global STORE
            STORE = None
            run(["hyprctl", "reload"])
            restart_idle()
            run(["hyprctl", "hyprpaper", "wallpaper", f",{SCHEMA['appearance.wallpaper'][2]}"])
            app.win.toast("All settings reset")

    PAGE_CLASSES = {
        "network": ("󰤨", "Network", NetworkPage), "bluetooth": ("󰂯", "Bluetooth", BluetoothPage),
        "sound": ("󰕾", "Sound", SoundPage), "displays": ("󰍹", "Displays", DisplaysPage),
        "appearance": ("󰏘", "Appearance", AppearancePage), "night": ("󰖔", "Night mode", NightPage),
        "notifications": ("󰂚", "Notifications", NotificationsPage), "input": ("󰌌", "Keyboard & mouse", InputPage),
        "power": ("󰒲", "Power & lock", PowerPage), "login": ("󰍂", "Login screen", LoginPage),
        "keys": ("󰋖", "Shortcuts", KeysPage), "about": ("󰋼", "About", AboutPage),
    }

    # ─────────────────────────── window ───────────────────────────
    class Win(Gtk.ApplicationWindow):
        def __init__(self, application):
            super().__init__(application=application, title="Settings")
            self.set_default_size(1040, 720)
            cls(self, "nothing-settings")
            # translucent window: Hyprland blurs what's behind the sidebar (macOS vibrancy)
            visual = self.get_screen().get_rgba_visual()
            if visual:
                self.set_visual(visual)
                self.set_app_paintable(True)
            overlay = Gtk.Overlay()
            self.add(overlay)
            root = Gtk.Box()
            overlay.add(root)

            side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            cls(side, "sidebar")
            # traffic lights: close · minimise (to the special workspace) · full screen
            lights = Gtk.Box(spacing=8)
            cls(lights, "traffic")
            for name, tip, act in (("close", "Close", self.close),
                                   ("min", "Minimise", lambda: spawn(["hyprctl", "dispatch",
                                    'hl.dsp.window.move({ workspace = "special:magic" })'])),
                                   ("zoom", "Full Screen", lambda: spawn(["hyprctl", "dispatch", "hl.dsp.window.fullscreen()"]))):
                b = Gtk.Button()
                cls(b, "light", name)
                b.set_tooltip_text(tip)
                b.connect("clicked", lambda _b, f=act: f())
                lights.pack_start(b, False, False, 0)
            side.pack_start(lights, False, False, 0)
            side.pack_start(lbl("Settings", "brand"), False, False, 0)
            self.nav = Gtk.ListBox()
            cls(self.nav, "nav")
            self.nav.connect("row-selected", lambda _l, r: r and self._show(r.page))
            for key in PAGES:
                icon, name, _ = PAGE_CLASSES[key]
                r = Gtk.ListBoxRow()
                r.page = key
                b = Gtk.Box(spacing=12)
                b.pack_start(lbl(icon, "nav-icon"), False, False, 0)
                b.pack_start(lbl(name, "nav-label"), False, False, 0)
                r.add(b)
                self.nav.add(r)
            side.pack_start(self.nav, True, True, 0)
            root.pack_start(side, False, False, 0)

            self.stack = Gtk.Stack()
            self.stack.set_hhomogeneous(False)   # one wide page must not widen the others
            self.stack.set_vhomogeneous(False)
            self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.stack.set_transition_duration(160)
            self.pages = {}
            for key in PAGES:
                p = PAGE_CLASSES[key][2]()
                self.pages[key] = p
                self.stack.add_named(p, key)
            root.pack_start(self.stack, True, True, 0)

            self.toast_rev = Gtk.Revealer()
            self.toast_rev.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
            self.toast_rev.set_halign(Gtk.Align.CENTER)
            self.toast_rev.set_valign(Gtk.Align.END)
            self.toast_lbl = lbl("", "toast", xalign=0.5)
            self.toast_rev.add(self.toast_lbl)
            overlay.add_overlay(self.toast_rev)
            self._toast_t = None
            self.connect("key-press-event", lambda _w, e: e.keyval == Gdk.KEY_Escape and (self.close(), True)[1])

        def _show(self, key):
            self.stack.set_visible_child_name(key)
            self.pages[key].show_page()

        def go(self, key):
            key = ALIASES.get(key, key)
            if key not in self.pages:
                key = "network"
            row = self.nav.get_row_at_index(PAGES.index(key))
            self.nav.select_row(row)
            self._show(key)

        def toast(self, msg, error=False):
            ctx = self.toast_lbl.get_style_context()
            (ctx.add_class if error else ctx.remove_class)("error")
            self.toast_lbl.set_text(msg)
            self.toast_rev.set_reveal_child(True)
            if self._toast_t:
                GLib.source_remove(self._toast_t)
            self._toast_t = GLib.timeout_add(4200 if error else 2600, self._hide_toast)

        def _hide_toast(self):
            self._toast_t = None
            self.toast_rev.set_reveal_child(False)
            return False

        def error(self, e):
            self.toast(str(e.args[0] if getattr(e, "args", None) else e)[:160], error=True)

        def ask(self, title, password=False):
            d = Gtk.Dialog(title=title, transient_for=self, modal=True)
            d.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Connect", Gtk.ResponseType.OK)
            d.set_default_response(Gtk.ResponseType.OK)
            e = Gtk.Entry()
            e.set_visibility(not password)
            e.set_activates_default(True)
            box = d.get_content_area()
            box.set_spacing(10)
            box.set_border_width(16)
            box.add(lbl(title, "row-title"))
            box.add(e)
            d.show_all()
            r = d.run()
            text = e.get_text()
            d.destroy()
            return text if r == Gtk.ResponseType.OK else None

        def confirm(self, question):
            d = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                                  buttons=Gtk.ButtonsType.YES_NO, text=question)
            r = d.run()
            d.destroy()
            return r == Gtk.ResponseType.YES

        def confirm_countdown(self, question, seconds):
            d = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                                  text=question)
            d.add_buttons("Revert", Gtk.ResponseType.CANCEL, "Keep", Gtk.ResponseType.OK)
            left = {"n": seconds}

            def tick():
                left["n"] -= 1
                d.format_secondary_text(f"Reverting in {left['n']} s…")
                if left["n"] <= 0:
                    d.response(Gtk.ResponseType.CANCEL)
                    return False
                return True
            d.format_secondary_text(f"Reverting in {seconds} s…")
            t = GLib.timeout_add(1000, tick)
            r = d.run()
            GLib.source_remove(t) if left["n"] > 0 else None
            d.destroy()
            return r == Gtk.ResponseType.OK

        def install(self, pkgs, then=None):
            self.toast(f"Installing {', '.join(pkgs)} — enter your password…")

            def done(r):
                rc, o, e = r
                if rc == 0:
                    self.toast(f"Installed {', '.join(pkgs)}")
                    if then:
                        then()
                else:
                    self.error(RuntimeError("cancelled" if rc in (126, 127) else (e or o or "install failed").splitlines()[-1]))
            bg(lambda: install_packages(pkgs), done)

    class App(Gtk.Application):
        def __init__(self):
            super().__init__(application_id="dev.nothing.Settings",
                             flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
            self.win = None

        def do_command_line(self, cmdline):
            args = cmdline.get_arguments()[1:]
            if not self.win:
                self._css()
                self.win = Win(self)
                self.win.show_all()
            self.win.go(args[0] if args else "network")
            self.win.present()
            return 0

        def _css(self):
            css = Gtk.CssProvider()
            css.load_from_path(os.path.join(HERE, "style.css"))
            Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                                     Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            APP_CSS.append(css)
            Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", theme_mode() == "dark")

    GLib.set_prgname("nothing-settings")
    app = App()
    if os.environ.get("NOTHING_SETTINGS_SELFTEST"):
        app.set_flags(Gio.ApplicationFlags.NON_UNIQUE)   # never attach to an open Settings window
        return selftest(app, Win, Gtk, PAGE_CLASSES)
    return app.run([sys.argv[0], page] if page else [sys.argv[0]])


def selftest(app, Win, Gtk, page_classes):
    """Open every page and fire every control with the backend replaced by recorders.
    Nothing real happens (no Wi-Fi changes, no installs, no lock). Exit code = failures."""
    calls, errors = [], []
    g = globals()
    actions = ["set_setting", "reset_setting", "wifi_power", "wifi_connect", "wifi_disconnect", "wifi_forget",
               "bt_power", "bt_action", "bt_scan", "pkexec", "install_packages", "spawn", "login_set",
               "dnd_set", "sound_default", "sound_volume", "sound_mute", "display_apply", "restart_idle",
               "theme_set", "widgets_cmd"]
    actions.append("brightness_set")
    for name in actions:
        g[name] = (lambda n: lambda *a, **k: calls.append((n, a)) or ((0, "", "") if n in ("pkexec", "install_packages") else None))(name)
    real_run = g["run"]

    def safe_run(cmd, *a, **k):          # read-only commands pass, anything that changes state is recorded
        c = cmd if isinstance(cmd, str) else " ".join(map(str, cmd))
        if any(w in c for w in (" set", "notif-clear", "pull", "install.sh", "reload", "suspend", "lock")):
            calls.append(("run", c))
            return 0, "", ""
        return real_run(cmd, *a, **k)
    g["run"] = safe_run
    sys.excepthook = lambda t, v, tb: errors.append(f"{t.__name__}: {v}")
    # dialogs answer themselves: no password, "no" to questions, revert displays, no file
    Win.ask = lambda self, *a, **k: calls.append(("dialog", a)) or None
    Win.confirm = lambda self, *a, **k: calls.append(("dialog", a)) or False
    Win.confirm_countdown = lambda self, *a, **k: calls.append(("dialog", a)) or False
    page_classes["appearance"][2]._add = lambda self: calls.append(("file-chooser", ()))
    page_classes["about"][2]._edit_local = lambda self: calls.append(("edit-local", ()))

    def walk(w):
        yield w
        if isinstance(w, Gtk.Container):
            for ch in w.get_children():
                yield from walk(ch)

    def pump(seconds=0.6):
        end = time.time() + seconds
        while time.time() < end:
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            time.sleep(0.02)

    def run_test():
        app.register(None)
        app._css()
        win = app.win = Win(app)
        win.show_all()
        report = []
        for key in PAGES:
            win.go(key)
            pump(6 if key in ("network", "bluetooth") else 1.2)   # lists load in the background
            page = win.pages[key]
            n = {"button": 0, "switch": 0, "combo": 0, "scale": 0, "spin": 0}
            for w in list(walk(page)):
                try:
                    if isinstance(w, Gtk.Switch):
                        w.set_active(not w.get_active()); n["switch"] += 1
                    elif isinstance(w, Gtk.SpinButton):
                        w.spin(Gtk.SpinType.STEP_FORWARD, 1); n["spin"] += 1
                    elif isinstance(w, Gtk.Button) and w.get_sensitive():
                        w.clicked(); n["button"] += 1
                    elif isinstance(w, Gtk.ComboBoxText):
                        m = w.get_model()
                        if m is not None and len(m) > 1:
                            w.set_active((w.get_active() + 1) % len(m)); n["combo"] += 1
                    elif isinstance(w, Gtk.Scale):
                        w.set_value(w.get_value() + w.get_adjustment().get_step_increment()); n["scale"] += 1
                except Exception as e:  # noqa: BLE001
                    errors.append(f"{key}: {type(e).__name__}: {e}")
                pump(0.05)
            pump(1.5)
            report.append((key, n))
        for key, n in report:
            print(f"  {key:<14} " + "  ".join(f"{v} {k}s" for k, v in n.items() if v))
        print(f"\n  {len(calls)} backend actions recorded, e.g.:")
        for c in calls[:12]:
            print("   ", c[0], str(c[1])[:90])
        print(f"\n  errors: {len(errors)}")
        for e in errors:
            print("   ", e)
        win.destroy()
        return len(errors)

    return run_test()


def main():
    argv = sys.argv[1:]
    # `nothing-settings wifi` opens the page; `nothing-settings wifi list` is the CLI
    if argv and (argv[0] not in PAGES and argv[0] not in ALIASES or len(argv) > 1):
        rc = cli(argv)
        if rc is not None:
            sys.exit(rc)
        print(f"nothing-settings: unknown command or page: {argv[0]}  (try --help)", file=sys.stderr)
        sys.exit(2)
    if argv and argv[0] == "dnd":
        sys.exit(cli(argv))
    sys.exit(gui(argv[0] if argv else None))


if __name__ == "__main__":
    main()
