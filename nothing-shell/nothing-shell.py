#!/usr/bin/env python3
"""nothing-shell — macOS-style shell surfaces for Hyprland.

A single GTK3 layer-shell daemon providing:
  • island   – workspace dots in the centre of the menu bar that morph into a
               panel on hover: clock, weather, calendar, MPRIS media, volume,
               network / bluetooth toggles.
  • control  – Control Center: Wi-Fi / Bluetooth / Mic, Focus, Night Shift,
               Light/Dark, sound, live CPU / memory / thermals, notifications, power.
  • widgets  – macOS desktop widgets on the wallpaper: Weather, Clock,
               Calendar and System (activity rings).

Usage:
  nothing-shell                      start the daemon (single instance)
  nothing-shell island  toggle|open|close|pin
  nothing-shell control toggle|open|close
  nothing-shell notif-status         JSON for the waybar bell
  nothing-shell notif-clear          clear notification history
  nothing-shell reload-css           re-read style.css and the theme palette (light / dark)
  nothing-shell quit
"""
import json
import math
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from hashlib import sha1

HOME = os.path.expanduser("~")
RUNTIME = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
SOCK = os.path.join(RUNTIME, "nothing-shell.sock")
CACHE = os.path.join(HOME, ".cache", "nothing-shell")
BIN = os.path.join(HOME, ".local", "bin")   # absolute: the session PATH may not include ~/.local/bin
NOTIF_FILE = os.path.join(CACHE, "notifications.json")
WEATHER_CACHE = os.path.join(HOME, ".cache", "nothing-weather.json")
WEATHER_SCRIPT = os.path.join(HOME, ".config", "waybar", "scripts", "weather.py")
CSS_FILE = os.environ.get("NOTHING_SHELL_CSS") or os.path.join(os.path.dirname(os.path.realpath(__file__)), "style.css")
OUTPUT = os.environ.get("NOTHING_OUTPUT", "")   # "" → the primary / first screen
WORKSPACES = range(1, int(os.environ.get("NOTHING_WORKSPACES", "10")) + 1)
PALETTE_FILE = os.path.join(HOME, ".config", "hypr", "theme", "palette.css")


def palette_value(name):
    """Raw value of `@define-color <name>` in the active theme's palette.css, aliases followed."""
    try:
        with open(PALETTE_FILE) as f:
            css = f.read()
    except OSError:
        return None
    for _ in range(4):   # follow aliases like `@define-color accent @blue;`
        m = re.search(r"@define-color\s+" + re.escape(name) + r"\s+([^;]+);", css)
        if not m:
            return None
        value = m.group(1).strip()
        if not value.startswith("@"):
            return value
        name = value[1:]
    return None


def palette(name, default):
    """A #rrggbb colour from the palette (for Pango markup)."""
    v = palette_value(name)
    return v if v and re.fullmatch(r"#[0-9a-fA-F]{6}", v) else default


def rgb(hexcolor):
    return tuple(int(hexcolor[i:i + 2], 16) / 255 for i in (1, 3, 5))


def parse_color(v):
    """#rrggbb or rgba(r, g, b, a) → (r, g, b, a) floats, or None."""
    if v and re.fullmatch(r"#[0-9a-fA-F]{6}", v):
        return rgb(v) + (1.0,)
    m = re.fullmatch(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)", v or "")
    if not m:
        return None
    return tuple(float(m.group(i)) / 255 for i in (1, 2, 3)) + (float(m.group(4) or 1),)


def rgba(name, default):
    """A palette colour as (r, g, b, a) floats, for cairo."""
    return parse_color(palette_value(name)) or parse_color(default)


# ───────────────────────────── client mode ─────────────────────────────
def send(cmd):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(SOCK)
        s.sendall(cmd.encode())
        s.shutdown(socket.SHUT_WR)
        reply = s.recv(65536).decode()
        s.close()
        return reply
    except OSError:
        return None


if len(sys.argv) > 1 and sys.argv[1] != "daemon":
    if sys.argv[1] == "notif-status" and not os.path.exists(SOCK):
        print('{"text":"󰂚","class":"none"}')
        sys.exit(0)
    r = send(" ".join(sys.argv[1:]))
    if r is None:
        print("nothing-shell: daemon not running", file=sys.stderr)
        sys.exit(1)
    if r:
        print(r)
    sys.exit(0)

if send("ping") == "pong":
    print("nothing-shell: already running")
    sys.exit(0)

# ───────────────────────────── daemon ─────────────────────────────
import cairo  # noqa: E402
import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
gi.require_version("Playerctl", "2.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, GtkLayerShell, Pango, PangoCairo, Playerctl  # noqa: E402

os.makedirs(os.path.join(CACHE, "art"), exist_ok=True)


# ───────────── helpers ─────────────
def run(cmd, timeout=2):
    try:
        return subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True,
                              text=True, timeout=timeout).stdout.strip()
    except Exception:
        return ""


def spawn(cmd):
    subprocess.Popen(cmd, shell=isinstance(cmd, str), start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def in_thread(fn, done=None):
    """Run fn in a worker thread, deliver its result to done() on the GTK loop."""
    def work():
        res = fn()
        if done:
            GLib.idle_add(done, res)
    threading.Thread(target=work, daemon=True).start()


def hyprctl_json(what):
    try:
        return json.loads(run(["hyprctl", "-j", what]) or "null")
    except ValueError:
        return None


def hypr_dispatch(lua):
    spawn(["hyprctl", "dispatch", lua])


def label(text="", cls=None, xalign=0.0, ellipsize=False, wrap=False, markup=False):
    lb = Gtk.Label()
    (lb.set_markup if markup else lb.set_text)(text)
    lb.set_xalign(xalign)
    if ellipsize:
        lb.set_ellipsize(Pango.EllipsizeMode.END)
    if wrap:
        lb.set_line_wrap(True)
        lb.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    if cls:
        for c in cls.split():
            lb.get_style_context().add_class(c)
    return lb


def add_cls(widget, *classes):
    ctx = widget.get_style_context()
    for c in classes:
        ctx.add_class(c)
    return widget


def set_cls(widget, cls, on):
    ctx = widget.get_style_context()
    (ctx.add_class if on else ctx.remove_class)(cls)


def box(vertical=False, spacing=0, cls=None):
    b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL if vertical else Gtk.Orientation.HORIZONTAL,
                spacing=spacing)
    if cls:
        add_cls(b, *cls.split())
    return b


def icon_button(glyph, cls="", tooltip=None, on_click=None):
    b = Gtk.Button()
    b.add(label(glyph, "glyph", xalign=0.5))
    add_cls(b, "nbtn", *cls.split())
    b.set_relief(Gtk.ReliefStyle.NONE)
    if tooltip:
        b.set_tooltip_text(tooltip)
    if on_click:
        b.connect("clicked", lambda *_: on_click())
    return b


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def time_ago(ts):
    d = int(time.time() - ts)
    if d < 60:
        return "now"
    if d < 3600:
        return f"{d // 60}m"
    if d < 86400:
        return f"{d // 3600}h"
    return f"{d // 86400}d"


def find_gdk_monitor(name):
    """Map a Hyprland output name to a Gdk.Monitor by geometry (GTK3 has no connector names)."""
    display = Gdk.Display.get_default()
    mons = hyprctl_json("monitors") or []
    target = next((m for m in mons if m.get("name") == name), None)
    for i in range(display.get_n_monitors()):
        m = display.get_monitor(i)
        g = m.get_geometry()
        if target and g.x == target["x"] and g.y == target["y"]:
            return m
    return display.get_primary_monitor() or display.get_monitor(0)


# ───────────── system state ─────────────
class Sys:
    _cpu_prev = None

    @classmethod
    def cpu(cls):
        with open("/proc/stat") as f:
            v = [int(x) for x in f.readline().split()[1:]]
        idle, total = v[3] + v[4], sum(v[:8])
        prev, cls._cpu_prev = cls._cpu_prev, (idle, total)
        if not prev or total == prev[1]:
            return 0.0
        return max(0.0, min(100.0, 100.0 * (1 - (idle - prev[0]) / (total - prev[1]))))

    @staticmethod
    def mem():
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                info[k] = int(v.split()[0])
        total, avail = info["MemTotal"], info["MemAvailable"]
        return (total - avail) / total * 100, (total - avail) / 1048576, total / 1048576

    @staticmethod
    def temps():
        """→ {'CPU': °C, 'GPU': °C, 'SSD': °C} from hwmon (k10temp/coretemp, amdgpu, nvme)."""
        out = {}
        base = "/sys/class/hwmon"
        wanted = {"k10temp": "CPU", "coretemp": "CPU", "zenpower": "CPU", "amdgpu": "GPU", "nvme": "SSD"}
        try:
            for h in sorted(os.listdir(base)):
                try:
                    name = open(f"{base}/{h}/name").read().strip()
                except OSError:
                    continue
                key = wanted.get(name)
                if not key or key in out:
                    continue
                try:
                    out[key] = int(open(f"{base}/{h}/temp1_input").read()) / 1000
                except OSError:
                    pass
        except OSError:
            pass
        return out

    @staticmethod
    def uptime():
        s = int(float(open("/proc/uptime").read().split()[0]))
        d, h, m = s // 86400, s % 86400 // 3600, s % 3600 // 60
        return f"Up {d} d {h} h" if d else f"Up {h} h {m} min"

    @staticmethod
    def volume():
        out = run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
        m = re.search(r"([\d.]+)", out)
        return (float(m.group(1)) * 100 if m else 0.0), "MUTED" in out

    @staticmethod
    def sink_name():
        out = run("wpctl inspect @DEFAULT_AUDIO_SINK@ | grep -m1 'node.description'")
        m = re.search(r'"(.*)"', out)
        return m.group(1) if m else "Output"

    @staticmethod
    def network():
        """→ (kind, name)  kind ∈ wifi|ethernet|offline"""
        out = run(["nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "device"])
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 3 and parts[1] == "connected":
                if parts[0] == "wifi":
                    return "wifi", parts[2]
                if parts[0] == "ethernet":
                    return "ethernet", parts[2]
        return "offline", "Offline"

    @staticmethod
    def wifi_on():
        return run(["nmcli", "radio", "wifi"]) == "enabled"

    @staticmethod
    def bt_available():
        # bluetoothctl blocks forever when bluetooth.service isn't running
        return os.path.isdir("/sys/class/bluetooth") and \
            run(["systemctl", "is-active", "bluetooth"]) == "active"

    @staticmethod
    def bt_on():
        return Sys.bt_available() and "Powered: yes" in run(["bluetoothctl", "show"])

    @staticmethod
    def dnd():
        return run(["swaync-client", "-D"]) == "true"

    @staticmethod
    def mic_on():
        return "MUTED" not in run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"])

    @staticmethod
    def night():
        base = os.environ.get("XDG_STATE_HOME", os.path.join(HOME, ".local", "state"))
        try:
            with open(os.path.join(base, "nothing", "night.json")) as f:
                return bool(json.load(f).get("on"))
        except (OSError, ValueError):
            return False

    @staticmethod
    def dark():
        """The active theme (nothing-theme): mac-dark → True, mac-light → False."""
        try:
            return not os.readlink(os.path.join(HOME, ".config", "hypr", "theme")).rstrip("/").endswith("light")
        except OSError:
            return True

    @staticmethod
    def recording():
        return run(["pgrep", "-x", "wf-recorder"]) != ""


WEATHER_ICONS = {
    "113": "󰖙", "116": "󰖕", "119": "󰖐", "122": "󰖐", "143": "󰖑", "248": "󰖑", "260": "󰖑",
    "176": "󰖗", "263": "󰖗", "266": "󰖗", "293": "󰖗", "296": "󰖗", "353": "󰖗",
    "299": "󰖖", "302": "󰖖", "305": "󰖖", "308": "󰖖", "356": "󰖖", "359": "󰖖",
    "179": "󰖘", "182": "󰙿", "185": "󰙿", "227": "󰼶", "230": "󰼶", "323": "󰖘", "326": "󰖘",
    "329": "󰼶", "332": "󰼶", "335": "󰼶", "338": "󰼶", "368": "󰖘", "371": "󰼶",
    "200": "󰙾", "386": "󰙾", "389": "󰙾", "392": "󰙾", "395": "󰙾",
}


# English names regardless of LC_TIME, like the menu-bar clock
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_ABBR = [d[:3] for d in DAY_NAMES]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]


def date_long(t=None):
    t = t or time.localtime()
    return f"{DAY_NAMES[t.tm_wday]}, {t.tm_mday} {MONTH_NAMES[t.tm_mon - 1]}"


def weather():
    try:
        with open(WEATHER_CACHE) as f:
            d = json.load(f)
        cur, days = d["current_condition"][0], d["weather"]
        area = d.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", "")
        try:   # day / night from today's sunrise & sunset (local time)
            astro = days[0]["astronomy"][0]
            now = time.strftime("%H:%M")
            to24 = lambda t: time.strftime("%H:%M", time.strptime(t, "%I:%M %p"))  # noqa: E731
            is_day = to24(astro["sunrise"]) <= now < to24(astro["sunset"])
        except (KeyError, IndexError, ValueError):
            is_day = 7 <= time.localtime().tm_hour < 19
        return {
            "code": cur["weatherCode"],
            "is_day": is_day,
            "hi": f'{days[0]["maxtempC"]}°',
            "lo": f'{days[0]["mintempC"]}°',
            "icon": WEATHER_ICONS.get(cur["weatherCode"], "󰖐"),
            "temp": f'{cur["temp_C"]}°',
            "cond": cur["weatherDesc"][0]["value"].strip(),
            "feels": f'{cur["FeelsLikeC"]}°',
            "hum": f'{cur["humidity"]}%',
            "wind": f'{cur["windspeedKmph"]} km/h',
            "area": area,
            "days": [(DAY_ABBR[time.strptime(x["date"], "%Y-%m-%d").tm_wday],
                      WEATHER_ICONS.get(x["hourly"][4]["weatherCode"], "󰖐"),
                      x["maxtempC"], x["mintempC"]) for x in days[:3]],
        }
    except Exception:
        return None


# ───────────── drawing (cairo) ─────────────
# Colours for everything drawn by hand; CSS widgets get theirs from palette.css directly.
# Re-read on `reload-css`, which nothing-theme sends after switching light / dark.
COL = {}
COLOR_DEFAULTS = {
    "fg": "#f5f5f7", "dim": "#a1a1a6", "mute": "#636366", "base": "#1e1e1e",
    "glass": "rgba(30, 30, 32, 0.55)", "line": "rgba(255, 255, 255, 0.12)",
    "highlight": "rgba(255, 255, 255, 0.10)", "track": "rgba(255, 255, 255, 0.16)",
    "accent": "#0a84ff", "blue": "#0a84ff", "green": "#30d158", "orange": "#ff9f0a",
    "red": "#ff453a", "indigo": "#5e5ce6", "yellow": "#ffd60a", "pink": "#ff375f",
    "teal": "#64d2ff", "purple": "#bf5af2",
}


def load_colors():
    for name, default in COLOR_DEFAULTS.items():
        COL[name] = rgba(name, default)
    COL["dark"] = sum(COL["base"][:3]) < 1.5


load_colors()


def rounded_rect(cr, x, y, w, h, r):
    r = max(0, min(r, w / 2, h / 2))
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def draw_text(cr, s, font, x, y, color, align="left", alpha=1.0, width=None):
    """Pango text at (x, y) = top-left (or top-centre / top-right). Returns (w, h)."""
    layout = PangoCairo.create_layout(cr)
    layout.set_font_description(Pango.FontDescription.from_string(font))
    if width:
        layout.set_width(int(width * Pango.SCALE))
        layout.set_ellipsize(Pango.EllipsizeMode.END)
    layout.set_text(s, -1)
    w, h = layout.get_pixel_size()
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    cr.move_to(x, y)
    cr.set_source_rgba(color[0], color[1], color[2], (color[3] if len(color) > 3 else 1) * alpha)
    PangoCairo.show_layout(cr, layout)
    return w, h


def set_rgba(cr, color, alpha=1.0):
    cr.set_source_rgba(color[0], color[1], color[2], (color[3] if len(color) > 3 else 1) * alpha)


class LineGraph(Gtk.DrawingArea):
    """History as a smooth line with a gradient fill (Activity Monitor style)."""

    def __init__(self, n=40, width=300, height=46, color="accent"):
        super().__init__()
        self.values, self.color = [0.0] * n, color
        self.set_size_request(width, height)
        self.connect("draw", self._draw)

    def _draw(self, _w, cr):
        W, H = self.get_allocated_width(), self.get_allocated_height()
        c = COL[self.color]
        n = len(self.values)
        pts = [(i * W / (n - 1), H - 2 - (H - 6) * min(v, 100) / 100) for i, v in enumerate(self.values)]
        cr.move_to(*pts[0])
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            mx = (x0 + x1) / 2
            cr.curve_to(mx, y0, mx, y1, x1, y1)
        path = cr.copy_path()
        cr.line_to(W, H)
        cr.line_to(0, H)
        cr.close_path()
        grad = cairo.LinearGradient(0, 0, 0, H)
        grad.add_color_stop_rgba(0, c[0], c[1], c[2], 0.45)
        grad.add_color_stop_rgba(1, c[0], c[1], c[2], 0.02)
        cr.set_source(grad)
        cr.fill()
        cr.append_path(path)
        cr.set_line_width(2)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        set_rgba(cr, c)
        cr.stroke()


class Bar(Gtk.DrawingArea):
    """Rounded progress bar: track + gradient fill."""

    def __init__(self, width=300, height=6, color="accent", color2=None):
        super().__init__()
        self.value, self.color, self.color2 = 0.0, color, color2
        self.set_size_request(width, height)
        self.set_valign(Gtk.Align.CENTER)
        self.connect("draw", self._draw)

    def set_value(self, v):
        self.value = max(0.0, min(100.0, v))
        self.queue_draw()

    def _draw(self, _w, cr):
        W, H = self.get_allocated_width(), self.get_allocated_height()
        rounded_rect(cr, 0, 0, W, H, H / 2)
        set_rgba(cr, COL["track"])
        cr.fill()
        fw = max(H, W * self.value / 100) if self.value > 0 else 0
        if fw:
            a, b = COL[self.color], COL[self.color2 or self.color]
            grad = cairo.LinearGradient(0, 0, fw, 0)
            grad.add_color_stop_rgba(0, a[0], a[1], a[2], 1)
            grad.add_color_stop_rgba(1, b[0], b[1], b[2], 1)
            rounded_rect(cr, 0, 0, fw, H, H / 2)
            cr.set_source(grad)
            cr.fill()


class EqBars(Gtk.DrawingArea):
    """Tiny animated equalizer shown next to the workspace dots while media plays."""

    def __init__(self):
        super().__init__()
        self.set_size_request(14, 12)
        self.set_valign(Gtk.Align.CENTER)   # don't stretch to the pill's full height
        self.phase = 0.0
        self.playing = False
        self._tick = None
        self.connect("draw", self._draw)

    def set_playing(self, playing):
        self.playing = playing
        self.set_visible(playing)
        if playing and not self._tick:
            self._tick = GLib.timeout_add(90, self._step)

    def _step(self):
        if not self.playing or not self.get_mapped():
            self._tick = None
            return False
        self.phase += 1
        self.queue_draw()
        return True

    def _draw(self, _w, cr):
        H = self.get_allocated_height()
        set_rgba(cr, COL["accent"])
        for c in range(3):
            h = 3 + (H - 3) * (0.5 + 0.5 * math.sin(self.phase * (0.5 + c * 0.23) + c * 1.9))
            rounded_rect(cr, c * 5, H - h, 3, h, 1.5)
            cr.fill()


class RoundedArt(Gtk.DrawingArea):
    """Album art with rounded corners; a colourful note placeholder when missing."""

    def __init__(self, size=92, radius=18):
        super().__init__()
        self.size, self.radius, self.pix = size, radius, None
        self.set_size_request(size, size)
        self.connect("draw", self._draw)

    def set_file(self, path):
        try:
            self.pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, self.size, self.size, False) if path else None
        except GLib.Error:
            self.pix = None
        self.queue_draw()

    def _draw(self, _w, cr):
        s = self.size
        rounded_rect(cr, 0, 0, s, s, self.radius)
        cr.clip()
        if self.pix:
            Gdk.cairo_set_source_pixbuf(cr, self.pix, 0, 0)
            cr.paint()
            return
        a, b = COL["pink"], COL["indigo"]
        grad = cairo.LinearGradient(0, 0, s, s)
        grad.add_color_stop_rgb(0, *a[:3])
        grad.add_color_stop_rgb(1, *b[:3])
        cr.set_source(grad)
        cr.paint()
        draw_text(cr, "\U000f075a", f"Symbols Nerd Font {int(s * 0.3)}", s / 2, s * 0.28, (1, 1, 1, 0.92), "center")


# ───────────── layer-shell base ─────────────
class LayerWindow(Gtk.Window):
    def __init__(self, namespace, anchors, margins, keyboard=False, layer=None):
        super().__init__()
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_namespace(self, namespace)
        GtkLayerShell.set_layer(self, layer or GtkLayerShell.Layer.TOP)
        GtkLayerShell.set_exclusive_zone(self, -1)
        GtkLayerShell.set_monitor(self, find_gdk_monitor(OUTPUT))
        for edge in anchors:
            GtkLayerShell.set_anchor(self, edge, True)
        for edge, px in margins.items():
            GtkLayerShell.set_margin(self, edge, px)
        GtkLayerShell.set_keyboard_mode(
            self, GtkLayerShell.KeyboardMode.ON_DEMAND if keyboard else GtkLayerShell.KeyboardMode.NONE)
        add_cls(self, "nothing-layer")

    def shrink(self):
        self.resize(1, 1)


# ═════════════════════════════ ISLAND ═════════════════════════════
class Island(LayerWindow):
    PANEL_W = 740
    HOVER_OPEN_MS = 160
    HOVER_CLOSE_MS = 520

    def __init__(self, shell):
        E = GtkLayerShell.Edge
        # OVERLAY so it sits above waybar's full-width surface; hidden while fullscreen.
        # Same top margin and height as the menu bar, so the compact island is the bar's centre.
        super().__init__("nothing-island", [E.TOP], {E.TOP: 4}, layer=GtkLayerShell.Layer.OVERLAY)
        self.shell = shell
        self.expanded = False
        self.pinned = False
        self._open_t = self._close_t = None
        self._anim = None
        self._compact_w = None

        self.ev = Gtk.EventBox()
        self.ev.set_above_child(False)
        self.ev.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK |
                           Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.SCROLL_MASK)
        self.ev.connect("enter-notify-event", self._on_enter)
        self.ev.connect("leave-notify-event", self._on_leave)
        self.ev.connect("button-press-event", self._on_click)
        self.ev.connect("scroll-event", self._on_scroll)
        self.add(self.ev)

        self.shell_box = box(vertical=True, cls="island")
        self.shell_box.set_halign(Gtk.Align.CENTER)
        self.ev.add(self.shell_box)

        # ── compact row: workspace dots (+ recording / now-playing / night / muted) ──
        self.compact = box(spacing=10, cls="island-compact")
        self.compact.set_halign(Gtk.Align.CENTER)
        self.rec = label("●", "rec-dot", xalign=0.5)
        self.eq = EqBars()
        self.ws_box = box(spacing=6, cls="ws")
        self.ws_box.set_valign(Gtk.Align.CENTER)
        self.ws_dots = {}
        for i in WORKSPACES:
            b = Gtk.Button()
            b.set_relief(Gtk.ReliefStyle.NONE)
            add_cls(b, "ws-dot")
            b.set_valign(Gtk.Align.CENTER)
            b.connect("clicked", lambda _b, n=i: hypr_dispatch(f"hl.dsp.focus({{ workspace = {n} }})"))
            self.ws_box.pack_start(b, False, False, 0)
            self.ws_dots[i] = b
        self.c_weather = label("", "c-weather")
        self.c_clock = label("", "c-clock", xalign=0.5)
        self.c_vol = label("", "c-vol")
        self.c_night = label("󰖔", "c-night")
        self.c_night.set_tooltip_text("Night mode")
        # (c_weather / c_clock stay unpacked: the menu bar shows the time on the right)
        for w in (self.rec, self.eq, self.ws_box, self.c_night, self.c_vol):
            self.compact.pack_start(w, False, False, 0)
        self.shell_box.pack_start(self.compact, False, False, 0)

        # ── expanded panel ──
        self.revealer = Gtk.Revealer()
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.revealer.set_transition_duration(300)
        self.revealer.connect("notify::child-revealed", self._on_revealed)
        self.panel = self._build_panel()
        self.revealer.add(self.panel)
        self.shell_box.pack_start(self.revealer, False, False, 0)

        self.show_all()
        self.revealer.set_visible(False)
        self.rec.set_visible(False)
        self.eq.set_visible(False)
        self.c_night.set_visible(False)
        self.refresh_compact()

    # ── panel layout ──
    def _build_panel(self):
        p = box(vertical=True, spacing=14, cls="island-panel")
        p.set_size_request(self.PANEL_W - 36, -1)

        # header: big clock + weather summary
        head = box(spacing=18)
        left = box(vertical=True, spacing=2)
        self.p_date = label("", "p-date")
        self.p_clock = label("", "p-clock")
        left.pack_start(self.p_date, False, False, 0)
        left.pack_start(self.p_clock, False, False, 0)
        head.pack_start(left, False, False, 0)

        wcard = box(spacing=16, cls="card weather-card")
        self.w_icon = label("", "w-icon", xalign=0.5)
        wtxt = box(vertical=True, spacing=2)
        self.w_temp = label("", "w-temp")
        self.w_cond = label("", "w-cond", ellipsize=True)
        self.w_meta = label("", "w-meta")
        for w in (self.w_temp, self.w_cond, self.w_meta):
            wtxt.pack_start(w, False, False, 0)
        self.w_days = box(spacing=14, cls="w-days")
        wcard.pack_start(self.w_icon, False, False, 0)
        wcard.pack_start(wtxt, True, True, 0)
        wcard.pack_start(self.w_days, False, False, 0)
        head.pack_end(wcard, True, True, 0)
        p.pack_start(head, False, False, 0)

        # calendar + media
        mid = box(spacing=14)
        cal_card = box(vertical=True, cls="card cal-card")
        self.cal = Gtk.Calendar()
        self.cal.set_display_options(Gtk.CalendarDisplayOptions.SHOW_HEADING |
                                     Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES)
        add_cls(self.cal, "ncal")
        cal_card.pack_start(self.cal, True, True, 0)
        mid.pack_start(cal_card, False, False, 0)
        mid.pack_start(self._build_media(), True, True, 0)
        p.pack_start(mid, False, False, 0)

        # quick controls
        q = box(spacing=10, cls="card quick-row")
        self.mute_btn = icon_button("󰕾", "round", "Mute", self._toggle_mute)
        self.vol = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol.set_draw_value(False)
        self.vol.set_hexpand(True)
        add_cls(self.vol, "nscale")
        self._vol_lock = False
        self._vol_pending = None
        self.vol.connect("value-changed", self._on_vol)
        volcol = box(vertical=True, spacing=2)
        self.sink_lbl = label("", "tiny dim", ellipsize=True)
        volcol.pack_start(self.sink_lbl, False, False, 0)
        volcol.pack_start(self.vol, False, False, 0)
        self.vol_pct = label("", "vol-pct", xalign=1)
        self.net_btn = Gtk.Button()
        add_cls(self.net_btn, "chip")
        self.net_lbl = label("", ellipsize=True)
        self.net_lbl.set_max_width_chars(14)
        self.net_btn.add(self.net_lbl)
        self.net_btn.connect("clicked", lambda *_: (self.collapse(force=True), spawn([os.path.join(BIN, "nothing-settings"), "network"])))
        self.wifi_t = icon_button("󰤨", "round toggle", "Wi-Fi", lambda: self.shell.toggle("wifi", self))
        self.bt_t = icon_button("󰂯", "round toggle", "Bluetooth", lambda: self.shell.toggle("bt", self))
        for w in (self.mute_btn,):
            q.pack_start(w, False, False, 0)
        q.pack_start(volcol, True, True, 0)
        q.pack_start(self.vol_pct, False, False, 0)
        q.pack_start(self.net_btn, False, False, 0)
        for w in (self.mute_btn, self.net_btn, self.wifi_t, self.bt_t):
            w.set_valign(Gtk.Align.CENTER)
        q.pack_start(self.wifi_t, False, False, 0)
        q.pack_start(self.bt_t, False, False, 0)
        p.pack_start(q, False, False, 0)
        return p

    def _build_media(self):
        card = box(spacing=16, cls="card media-card")
        self.art = RoundedArt(108, 22)
        self.art.set_valign(Gtk.Align.CENTER)
        card.pack_start(self.art, False, False, 0)
        col = box(vertical=True, spacing=4)
        top = box(spacing=8)
        self.m_player = label("Not Playing", "m-player")
        self.m_cycle = icon_button("󰒝", "mini", "Next player", self.shell.media.cycle)
        top.pack_start(self.m_player, False, False, 0)
        top.pack_end(self.m_cycle, False, False, 0)
        self.m_title = label("Nothing playing", "m-title", ellipsize=True)
        self.m_artist = label("—", "m-artist dim", ellipsize=True)
        self.m_bar = Bar(width=260, height=5, color="fg")
        self.m_time = label("", "tiny dim")
        ctr = box(spacing=10)
        ctr.set_halign(Gtk.Align.START)
        self.m_prev = icon_button("󰒮", "round", "Previous", lambda: self.shell.media.do("previous"))
        self.m_play = icon_button("󰐊", "round play", "Play / Pause", lambda: self.shell.media.do("play_pause"))
        self.m_next = icon_button("󰒭", "round", "Next", lambda: self.shell.media.do("next"))
        for w in (self.m_prev, self.m_play, self.m_next):
            ctr.pack_start(w, False, False, 0)
        for w in (top, self.m_title, self.m_artist):
            col.pack_start(w, False, False, 0)
        col.pack_start(self.m_bar, False, False, 6)
        bottom = box(spacing=8)
        bottom.pack_start(ctr, False, False, 0)
        bottom.pack_end(self.m_time, False, False, 0)
        col.pack_start(bottom, False, False, 0)
        card.pack_start(col, True, True, 0)
        return card

    # ── hover / click ──
    def _on_enter(self, _w, ev):
        if ev.detail == Gdk.NotifyType.INFERIOR:
            return
        if self._close_t:
            GLib.source_remove(self._close_t)
            self._close_t = None
        if not self.expanded and not self._open_t:
            self._open_t = GLib.timeout_add(self.HOVER_OPEN_MS, self._hover_open)

    def _on_leave(self, _w, ev):
        if ev.detail == Gdk.NotifyType.INFERIOR or ev.mode != Gdk.CrossingMode.NORMAL:
            return
        if self._open_t:
            GLib.source_remove(self._open_t)
            self._open_t = None
        if self.expanded and not self.pinned and not self._close_t:
            self._close_t = GLib.timeout_add(self.HOVER_CLOSE_MS, self._hover_close)

    def _hover_open(self):
        self._open_t = None
        self.expand()
        return False

    def _hover_close(self):
        self._close_t = None
        self.collapse()
        return False

    def _on_click(self, _w, ev):
        if ev.y > self.compact.get_allocated_height() + 4:
            return False  # clicks inside the expanded panel belong to its widgets
        if ev.button == 1:
            if self.expanded and self.pinned:
                self.collapse(force=True)
            else:
                self.pinned = True
                self.expand()
        elif ev.button == 3:
            self.shell.control.toggle()
        return False

    def _on_scroll(self, _w, ev):
        d = "e+1" if ev.direction == Gdk.ScrollDirection.DOWN else "e-1"
        if ev.direction in (Gdk.ScrollDirection.UP, Gdk.ScrollDirection.DOWN):
            hypr_dispatch(f'hl.dsp.focus({{ workspace = "{d}" }})')

    # ── morph animation ──
    def _animate_width(self, w_from, w_to, ms, then=None):
        if self._anim:
            self.remove_tick_callback(self._anim)
        start = None

        def tick(_w, clock):
            nonlocal start
            now = clock.get_frame_time() / 1000
            if start is None:
                start = now
            t = min(1.0, (now - start) / ms)
            w = int(w_from + (w_to - w_from) * ease_out_cubic(t))
            self.shell_box.set_size_request(w, -1)
            if w_to < w_from:
                self.shrink()
            if t >= 1:
                self._anim = None
                if then:
                    then()
                return False
            return True

        self._anim = self.add_tick_callback(tick)

    def expand(self):
        if self.expanded:
            return
        self.expanded = True
        set_cls(self.shell_box, "expanded", True)
        self.refresh_panel()
        self.shell.media.refresh()
        self._compact_w = self.compact.get_allocated_width() + 28
        self._animate_width(self._compact_w, self.PANEL_W, 220, self._reveal)
        if not getattr(self, "_live", None):
            self._live = GLib.timeout_add(1000, self._live_tick)

    def _reveal(self):
        if self.expanded:
            self.revealer.set_visible(True)
            self.revealer.set_reveal_child(True)

    def collapse(self, force=False):
        if not self.expanded:
            return
        if force:
            self.pinned = False
        self.expanded = False
        self.pinned = False
        self.revealer.set_reveal_child(False)

    def _on_revealed(self, *_):
        if self.revealer.get_child_revealed() or self.expanded:
            return
        self.revealer.set_visible(False)
        set_cls(self.shell_box, "expanded", False)
        target = self.compact.get_preferred_width()[1] + 28
        self._animate_width(self.PANEL_W, target, 200, self._finish_collapse)

    def _finish_collapse(self):
        self.shell_box.set_size_request(-1, -1)
        self.shrink()

    def toggle(self, how="toggle"):
        if how == "open" or (how in ("toggle", "pin") and not self.expanded):
            self.pinned = True
            self.expand()
        elif how == "close" or self.expanded:
            self.collapse(force=True)

    def _live_tick(self):
        if not self.expanded:
            self._live = None
            return False
        self.refresh_panel(light=True)
        self.shell.media.update_position()
        return True

    # ── data ──
    def set_workspaces(self, active, occupied, urgent=()):
        for i, b in self.ws_dots.items():
            set_cls(b, "active", i == active)
            set_cls(b, "occupied", i in occupied)
            set_cls(b, "urgent", i in urgent)

    def refresh_compact(self):
        self.c_clock.set_text(time.strftime("%H:%M"))
        w = weather()
        self.c_weather.set_text(f"{w['icon']}  {w['temp']}" if w else "󰖐  --")
        self.rec.set_visible(Sys.recording())
        vol, muted = Sys.volume()
        self.c_vol.set_visible(muted)
        self.c_vol.set_text("󰝟")
        self.c_night.set_visible(Sys.night())

    def refresh_panel(self, light=False):
        self.p_clock.set_text(time.strftime("%-I:%M"))
        self.p_date.set_text(date_long())
        if not self._vol_lock:
            vol, muted = Sys.volume()
            self._vol_lock = True
            self.vol.set_value(vol)
            self._vol_lock = False
            self.vol_pct.set_text(f"{int(round(vol))}")
            self.mute_btn.get_child().set_text("󰝟" if muted else "󰕾")
            set_cls(self.mute_btn, "on", not muted)
        if light:
            return
        w = weather()
        if w:
            self.w_icon.set_text(w["icon"])
            self.w_temp.set_text(w["temp"])
            self.w_cond.set_text(w["cond"])
            self.w_meta.set_text(f"{w['area']} · Feels {w['feels']} · {w['hum']}")
            for c in self.w_days.get_children():
                self.w_days.remove(c)
            for day, ic, hi, lo in w["days"]:
                col = box(vertical=True, spacing=2, cls="w-day")
                col.pack_start(label(day, "tiny dim", xalign=0.5), False, False, 0)
                col.pack_start(label(ic, "w-day-icon", xalign=0.5), False, False, 0)
                col.pack_start(label(f"{hi}°/{lo}°", "tiny", xalign=0.5), False, False, 0)
                self.w_days.pack_start(col, False, False, 0)
            self.w_days.show_all()
        else:
            self.w_icon.set_text("󰖑")
            self.w_temp.set_text("--")
            self.w_cond.set_text("Weather unavailable")
        today = time.localtime()
        self.cal.select_month(today.tm_mon - 1, today.tm_year)
        self.cal.select_day(today.tm_mday)
        in_thread(lambda: (Sys.network(), Sys.wifi_on(), Sys.bt_on(), Sys.sink_name()), self._apply_net)

    def _apply_net(self, res):
        (kind, name), wifi, bt, sink = res
        glyph = {"wifi": "󰤨", "ethernet": "󰈀", "offline": "󰤭"}[kind]
        self.net_lbl.set_text(f"{glyph}  {name}")
        set_cls(self.net_btn, "offline", kind == "offline")
        set_cls(self.wifi_t, "on", wifi)
        set_cls(self.bt_t, "on", bt)
        self.sink_lbl.set_text(sink)

    def _on_vol(self, scale):
        if self._vol_lock:
            return
        v = scale.get_value()
        self.vol_pct.set_text(f"{int(v)}")
        if self._vol_pending is None:
            self._vol_pending = GLib.timeout_add(40, self._apply_vol)

    def _apply_vol(self):
        self._vol_pending = None
        spawn(["wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", f"{self.vol.get_value() / 100:.2f}"])
        return False

    def _toggle_mute(self):
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
        self.refresh_panel(light=True)
        self.refresh_compact()


# ═════════════════════════════ MEDIA ═════════════════════════════
class Media:
    """MPRIS via Playerctl: tracks all players, follows the one that played last."""

    def __init__(self, shell):
        self.shell = shell
        self.manager = Playerctl.PlayerManager()
        self.manager.connect("name-appeared", self._on_name)
        self.manager.connect("player-vanished", lambda *_: self.refresh())
        self.current = None
        for name in self.manager.props.player_names:
            self._on_name(self.manager, name)
        self._art_url = None

    def _on_name(self, _m, name):
        try:
            p = Playerctl.Player.new_from_name(name)
        except GLib.Error:
            return
        p.connect("playback-status", self._on_status)
        p.connect("metadata", lambda *_: self.refresh())
        self.manager.manage_player(p)
        self.refresh()

    def _on_status(self, player, status):
        if status == Playerctl.PlaybackStatus.PLAYING:
            self.current = player
        self.refresh()

    def players(self):
        return list(self.manager.props.players)

    def active(self):
        ps = self.players()
        if not ps:
            return None
        if self.current in ps:
            return self.current
        playing = [p for p in ps if p.props.playback_status == Playerctl.PlaybackStatus.PLAYING]
        self.current = (playing or ps)[0]
        return self.current

    def cycle(self):
        ps = self.players()
        if len(ps) > 1:
            i = ps.index(self.current) if self.current in ps else -1
            self.current = ps[(i + 1) % len(ps)]
            self.refresh()

    def do(self, action):
        p = self.active()
        if p:
            try:
                getattr(p, action)()
            except GLib.Error:
                pass
        GLib.timeout_add(150, lambda: (self.refresh(), False)[1])

    def _meta(self, p, key):
        try:
            v = p.print_metadata_prop(key)
            return v or ""
        except GLib.Error:
            return ""

    def refresh(self):
        isl = self.shell.island
        if not isl:
            return
        p = self.active()
        playing = bool(p) and p.props.playback_status == Playerctl.PlaybackStatus.PLAYING
        isl.eq.set_playing(playing)
        isl.m_cycle.set_visible(len(self.players()) > 1)
        if not p:
            isl.m_player.set_text("Not Playing")
            isl.m_title.set_text("Nothing playing")
            isl.m_artist.set_text("Start Spotify, YouTube or any MPRIS player")
            isl.m_play.get_child().set_text("󰐊")
            isl.m_bar.set_value(0)
            isl.m_time.set_text("")
            isl.art.set_file(None)
            self._art_url = None
            return
        name = (p.props.player_name or "player").split(".")[0]
        isl.m_player.set_text(("● " if playing else "") + name.capitalize())
        set_cls(isl.m_player, "live", playing)
        isl.m_title.set_text(self._meta(p, "xesam:title") or "Unknown title")
        isl.m_artist.set_text(self._meta(p, "xesam:artist") or self._meta(p, "xesam:album") or name.title())
        isl.m_play.get_child().set_text("󰏤" if playing else "󰐊")
        set_cls(isl.m_play, "on", playing)
        self._load_art(self._meta(p, "mpris:artUrl"))
        self.update_position()

    def update_position(self):
        isl = self.shell.island
        p = self.active()
        if not p or not isl:
            return
        try:
            length = int(self._meta(p, "mpris:length") or 0)
            pos = p.get_position()
        except (GLib.Error, ValueError):
            length, pos = 0, 0
        if length > 0:
            isl.m_bar.set_value(pos / length * 100)
            f = lambda us: f"{us // 60_000_000}:{us // 1_000_000 % 60:02d}"  # noqa: E731
            isl.m_time.set_text(f"{f(pos)} / {f(length)}")
        else:
            isl.m_bar.set_value(0)
            isl.m_time.set_text("Live" if p.props.playback_status == Playerctl.PlaybackStatus.PLAYING else "")

    def _load_art(self, url):
        if url == self._art_url:
            return
        self._art_url = url
        isl = self.shell.island
        if not url:
            isl.art.set_file(None)
            return
        if url.startswith("file://"):
            isl.art.set_file(urllib.parse.unquote(url[7:]))
            return
        path = os.path.join(CACHE, "art", sha1(url.encode()).hexdigest())

        def fetch():
            if not os.path.exists(path):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "nothing-shell"})
                    with urllib.request.urlopen(req, timeout=6) as r, open(path, "wb") as f:
                        f.write(r.read())
                except Exception:
                    return None
            return path

        in_thread(fetch, lambda p: isl.art.set_file(p) if self._art_url == url else None)


# ═════════════════════════════ NOTIFICATIONS ═════════════════════════════
class NotifyLog:
    """Passive D-Bus monitor of org.freedesktop.Notifications.Notify (swaync stays the daemon)."""

    def __init__(self, shell):
        self.shell = shell
        try:
            with open(NOTIF_FILE) as f:
                self.items = json.load(f)
        except (OSError, ValueError):
            self.items = []
        self._next = max([n["id"] for n in self.items], default=0) + 1
        try:
            addr = Gio.dbus_address_get_for_bus_sync(Gio.BusType.SESSION, None)
            self.conn = Gio.DBusConnection.new_for_address_sync(
                addr, Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT |
                Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION, None, None)
            self.conn.call_sync(
                "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus.Monitoring",
                "BecomeMonitor",
                GLib.Variant("(asu)", (["type='method_call',interface='org.freedesktop.Notifications',"
                                        "member='Notify'"], 0)),
                None, Gio.DBusCallFlags.NONE, -1, None)
            self.conn.add_filter(self._filter)
        except GLib.Error as e:
            print("notification monitor unavailable:", e.message, file=sys.stderr)

    def _filter(self, _conn, msg, _incoming):
        try:
            if msg.get_member() == "Notify":
                body = msg.get_body().unpack()
                GLib.idle_add(self._add, body)
        except Exception:
            pass
        return None

    def _add(self, body):
        app, _rid, icon, summary, text, _actions, hints, _timeout = body
        if hints.get("transient") or not (summary or text):
            return False
        text = re.sub(r"<[^>]+>", "", text or "")
        self.items.insert(0, {"id": self._next, "app": app or "System", "icon": icon or "",
                              "summary": summary, "body": text, "ts": time.time()})
        self._next += 1
        self.items = self.items[:60]
        self._save()
        return False

    def dismiss(self, nid):
        self.items = [n for n in self.items if n["id"] != nid]
        self._save()

    def clear(self):
        self.items = []
        spawn(["swaync-client", "-C"])
        self._save()

    def status(self):
        dnd = Sys.dnd()
        n = len(self.items)
        glyph = "󰂛" if dnd else "󰂚"
        return json.dumps(ensure_ascii=False, obj={"text": glyph + (f"<span foreground='{palette('accent', '#9dad94')}'><sup>●</sup></span>" if n else ""),
                           "class": ("dnd " if dnd else "") + ("has" if n else "none"),
                           "tooltip": f"{n} notification{'s' if n != 1 else ''}" + (" · DND" if dnd else "")})

    def _save(self):
        tmp = NOTIF_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.items, f)
        os.replace(tmp, NOTIF_FILE)
        spawn("pkill -RTMIN+9 waybar")
        if self.shell.control:
            self.shell.control.render_notifs()


# ═════════════════════════════ CONTROL CENTER ═════════════════════════════
class Control(LayerWindow):
    WIDTH = 344

    def __init__(self, shell):
        E = GtkLayerShell.Edge
        # under the menu bar (4 + 34 px), right-aligned with it
        super().__init__("nothing-control", [E.TOP, E.RIGHT], {E.TOP: 46, E.RIGHT: 8}, keyboard=True)
        self.shell = shell
        self.open = False
        self._confirm = {}
        self.connect("key-press-event", self._on_key)
        self._had_focus = False   # "has the pointer been inside since opening"
        self._leave_t = None
        self._vol_lock = False
        self._vol_t = None
        self.toggles, self.subs = {}, {}

        # open/close animation comes from Hyprland's layer rule (slide in from the right)
        ev = Gtk.EventBox()
        ev.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        ev.connect("enter-notify-event", self._on_enter)
        ev.connect("leave-notify-event", self._on_leave)
        self.add(ev)
        root = box(vertical=True, spacing=10, cls="control")
        root.set_size_request(self.WIDTH, -1)
        ev.add(root)
        inner = self.WIDTH - 2 * 12 - 2 * 14   # panel padding + module padding

        # ── connectivity · Focus · Night Shift · Appearance ──
        top = box(spacing=10)
        top.set_homogeneous(True)
        conn = box(vertical=True, spacing=12, cls="cc-module")
        for key, glyph, name in (("wifi", "\U000f05a9", "Wi-Fi"), ("bt", "\U000f00af", "Bluetooth"),
                                 ("mic", "\U000f036c", "Microphone")):
            conn.pack_start(self._conn_row(key, glyph, name), False, False, 0)
        top.pack_start(conn, True, True, 0)
        right = box(vertical=True, spacing=10)
        focus = box(cls="cc-module cc-wide")
        focus.pack_start(self._conn_row("dnd", "\U000f009b", "Focus"), True, True, 0)
        right.pack_start(focus, True, True, 0)
        squares = box(spacing=10)
        squares.set_homogeneous(True)
        squares.pack_start(self._square("night", "\U000f0594", "Night Shift"), True, True, 0)
        squares.pack_start(self._square("dark", "\U000f050e", "Dark Mode"), True, True, 0)
        right.pack_start(squares, True, True, 0)
        top.pack_start(right, True, True, 0)
        root.pack_start(top, False, False, 0)

        # ── sound ──
        snd = box(vertical=True, spacing=8, cls="cc-module")
        head = box(spacing=8)
        head.pack_start(label("Sound", "cc-name"), False, False, 0)
        self.sink = label("", "cc-sub", xalign=1, ellipsize=True)
        self.sink.set_max_width_chars(24)
        head.pack_end(self.sink, False, False, 0)
        snd.pack_start(head, False, False, 0)
        self.vol = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol.set_draw_value(False)
        add_cls(self.vol, "ccscale")
        self.vol.connect("value-changed", self._on_vol)
        snd.pack_start(self.vol, False, False, 0)
        root.pack_start(snd, False, False, 0)

        # ── system: CPU history, memory, thermals ──
        sysm = box(vertical=True, spacing=8, cls="cc-module")
        row = box()
        row.pack_start(label("CPU", "cc-name"), False, False, 0)
        self.cpu_pct = label("", "stat-val", xalign=1)
        row.pack_end(self.cpu_pct, False, False, 0)
        sysm.pack_start(row, False, False, 0)
        self.graph = LineGraph(n=40, width=inner, height=44, color="accent")
        sysm.pack_start(self.graph, False, False, 0)
        row2 = box()
        row2.pack_start(label("Memory", "cc-name"), False, False, 0)
        self.ram_txt = label("", "stat-val", xalign=1)
        row2.pack_end(self.ram_txt, False, False, 0)
        sysm.pack_start(row2, False, False, 4)
        self.ram_bar = Bar(width=inner, height=6, color="green", color2="teal")
        sysm.pack_start(self.ram_bar, False, False, 0)
        th = box(spacing=8, cls="thermals")
        th.set_homogeneous(True)
        self.temps = {}
        for key in ("CPU", "GPU", "SSD"):
            t = box(vertical=True, spacing=0, cls="temp-tile")
            t.pack_start(label(key, "cc-sub", xalign=0.5), False, False, 0)
            v = label("--", "temp-val", xalign=0.5)
            t.pack_start(v, False, False, 0)
            th.pack_start(t, True, True, 0)
            self.temps[key] = (t, v)
        sysm.pack_start(th, False, False, 4)
        self.uptime = label("", "cc-sub", xalign=0.5)
        sysm.pack_start(self.uptime, False, False, 0)
        root.pack_start(sysm, False, False, 0)

        # ── notifications ──
        nh = box(spacing=8)
        self.n_title = label("Notifications", "section")
        nh.pack_start(self.n_title, False, False, 0)
        clear = Gtk.Button(label="Clear")
        add_cls(clear, "chip", "danger-hover")
        clear.connect("clicked", lambda *_: self.shell.notifs.clear())
        nh.pack_end(clear, False, False, 0)
        root.pack_start(nh, False, False, 0)
        self.n_scroll = Gtk.ScrolledWindow()
        self.n_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.n_list = box(vertical=True, spacing=8)
        self.n_scroll.add(self.n_list)
        root.pack_start(self.n_scroll, False, False, 0)

        # ── power ──
        pw = box(spacing=6, cls="power-row")
        pw.set_homogeneous(True)
        for key, glyph, name, cmd, confirm in (
                ("lock", "\U000f033e", "Lock", "loginctl lock-session", False),
                ("sleep", "\U000f0904", "Sleep", "systemctl suspend", False),
                ("logout", "\U000f0343", "Log Out", "hyprctl dispatch 'hl.dsp.exit()'", True),
                ("reboot", "\U000f0709", "Restart", "systemctl reboot", True),
                ("power", "\U000f0425", "Shut Down", "systemctl poweroff", True)):
            b = Gtk.Button()
            add_cls(b, "power-btn")
            col = box(vertical=True, spacing=4)
            circ = label(glyph, "glyph power-circle", xalign=0.5)
            circ.set_halign(Gtk.Align.CENTER)
            col.pack_start(circ, False, False, 0)
            lbl = label(name, "tiny", xalign=0.5)
            col.pack_start(lbl, False, False, 0)
            b.add(col)
            b.connect("clicked", lambda _b, k=key, c=cmd, cf=confirm, l=lbl, n=name: self._power(k, c, cf, _b, l, n))
            pw.pack_start(b, True, True, 0)
        root.pack_start(pw, False, False, 0)

        self.show_all()
        self.hide()
        self.render_notifs()

    # ── building blocks ──
    def _circle(self, key, glyph):
        b = Gtk.Button()
        add_cls(b, "cc-circle")
        b.add(label(glyph, "glyph", xalign=0.5))
        b.set_valign(Gtk.Align.CENTER)
        b.connect("clicked", lambda _b: self.shell.toggle(key, self))
        self.toggles[key] = b
        return b

    def _conn_row(self, key, glyph, name):
        row = box(spacing=10)
        row.pack_start(self._circle(key, glyph), False, False, 0)
        col = box(vertical=True)
        col.set_valign(Gtk.Align.CENTER)
        col.pack_start(label(name, "cc-name"), False, False, 0)
        sub = label("", "cc-sub", ellipsize=True)
        sub.set_max_width_chars(11)
        col.pack_start(sub, False, False, 0)
        self.subs[key] = sub
        row.pack_start(col, True, True, 0)
        return row

    def _square(self, key, glyph, name):
        m = box(vertical=True, spacing=6, cls="cc-module cc-square")
        c = self._circle(key, glyph)
        c.set_halign(Gtk.Align.CENTER)
        m.pack_start(c, False, False, 0)
        m.pack_start(label(name, "cc-sub", xalign=0.5), False, False, 0)
        return m

    def _on_vol(self, _scale):
        if self._vol_lock:
            return
        if self._vol_t is None:
            self._vol_t = GLib.timeout_add(40, self._apply_vol)

    def _apply_vol(self):
        self._vol_t = None
        spawn(["wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", f"{self.vol.get_value() / 100:.2f}"])
        return False

    # ── power with two-step confirm ──
    def _power(self, key, cmd, confirm, btn, lbl, name):
        if confirm and key not in self._confirm:
            set_cls(btn, "confirm", True)
            lbl.set_text("Confirm?")

            def reset():
                self._confirm.pop(key, None)
                set_cls(btn, "confirm", False)
                lbl.set_text(name)
                return False
            self._confirm[key] = GLib.timeout_add(2600, reset)
            return
        if key in self._confirm:
            GLib.source_remove(self._confirm.pop(key))
        self.close()
        GLib.timeout_add(280, lambda: (spawn(cmd), False)[1])

    # ── notifications ──
    def render_notifs(self):
        for c in self.n_list.get_children():
            self.n_list.remove(c)
        items = self.shell.notifs.items if self.shell.notifs else []
        self.n_title.set_text(f"Notifications · {len(items)}" if items else "Notifications")
        if not items:
            e = box(vertical=True, spacing=6, cls="empty")
            e.pack_start(label("· · ·", "empty-dots", xalign=0.5), False, False, 0)
            e.pack_start(label("All caught up", "tiny dim", xalign=0.5), False, False, 0)
            self.n_list.pack_start(e, False, False, 0)
        for n in items[:30]:
            card = box(spacing=10, cls="card notif")
            col = box(vertical=True, spacing=2)
            top = box(spacing=6)
            top.pack_start(label(n["app"], "n-app"), False, False, 0)
            top.pack_start(label(time_ago(n["ts"]), "tiny dim"), False, False, 0)
            col.pack_start(top, False, False, 0)
            col.pack_start(label(n["summary"], "n-sum", ellipsize=True), False, False, 0)
            if n["body"]:
                b = label(n["body"], "n-body dim", wrap=True)
                b.set_lines(2)
                b.set_ellipsize(Pango.EllipsizeMode.END)
                b.set_max_width_chars(40)
                col.pack_start(b, False, False, 0)
            card.pack_start(col, True, True, 0)
            x = icon_button("󰅖", "mini", "Dismiss", lambda nid=n["id"]: self.shell.notifs.dismiss(nid))
            x.set_valign(Gtk.Align.START)
            card.pack_end(x, False, False, 0)
            self.n_list.pack_start(card, False, False, 0)
        self.n_list.show_all()
        # GTK3 scrolled windows ignore their child's natural height → size it ourselves
        h = sum(c.get_preferred_height()[1] + 8 for c in self.n_list.get_children())
        self.n_scroll.set_min_content_height(max(70, min(h, 300)))
        self.shrink()

    # ── open / close ──
    def toggle(self, how="toggle"):
        if how == "open" or (how == "toggle" and not self.open):
            self.show_()
        else:
            self.close()

    def show_(self):
        if self.open:
            return
        self.open = True
        self._had_focus = False
        self.shell.island.collapse(force=True)
        self.refresh()
        self.render_notifs()
        self.show()
        self.present()
        self._live = GLib.timeout_add(1000, self._tick)

    def close(self):
        if not self.open:
            return
        self.open = False
        self.hide()

    def _on_key(self, _w, ev):
        if ev.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    def _on_enter(self, _w, ev):
        if ev.detail == Gdk.NotifyType.INFERIOR:
            return
        self._had_focus = True
        if self._leave_t:
            GLib.source_remove(self._leave_t)
            self._leave_t = None

    def _on_leave(self, _w, ev):
        if ev.detail == Gdk.NotifyType.INFERIOR or ev.mode != Gdk.CrossingMode.NORMAL:
            return
        if self._had_focus and self.open and not self._leave_t:
            self._leave_t = GLib.timeout_add(900, self._leave_close)

    def _leave_close(self):
        self._leave_t = None
        self.close()
        return False

    def _tick(self):
        if not self.open:
            return False
        self.refresh()
        return True

    def refresh(self):
        c = self.shell.cpu_last
        self.cpu_pct.set_text(f"{c:.0f}%")
        self.graph.values = list(self.shell.cpu_hist)
        self.graph.queue_draw()
        pct, used, total = Sys.mem()
        self.ram_txt.set_text(f"{used:.1f} of {total:.0f} GB")
        self.ram_bar.set_value(pct)
        self.uptime.set_text(Sys.uptime())
        limits = {"CPU": 85, "GPU": 90, "SSD": 70}
        for k, v in Sys.temps().items():
            tile, lbl = self.temps[k]
            lbl.set_text(f"{v:.0f}°")
            set_cls(tile, "hot", v >= limits[k])
        in_thread(lambda: {"wifi": Sys.wifi_on(), "bt": Sys.bt_on(), "dnd": Sys.dnd(), "mic": Sys.mic_on(),
                            "night": Sys.night(), "dark": Sys.dark(), "net": Sys.network(),
                            "vol": Sys.volume(), "sink": Sys.sink_name()},
                  self._apply_toggles)

    def _apply_toggles(self, st):
        for k in self.toggles:
            set_cls(self.toggles[k], "on", bool(st[k]))
        kind, name = st["net"]
        self.subs["wifi"].set_text(name if kind == "wifi" else "Ethernet" if kind == "ethernet"
                                   else "Not Connected" if st["wifi"] else "Off")
        self.subs["bt"].set_text("On" if st["bt"] else "Off")
        self.subs["mic"].set_text("On" if st["mic"] else "Muted")
        self.subs["dnd"].set_text("Do Not Disturb" if st["dnd"] else "Off")
        vol, muted = st["vol"]
        self._vol_lock = True
        self.vol.set_value(0 if muted else vol)
        self._vol_lock = False
        self.sink.set_text(st["sink"])


# ═════════════════════════════ DESKTOP WIDGETS ═════════════════════════════
# macOS-style widgets on the wallpaper (bottom layer, under windows): Weather and Clock
# (small), Calendar and System (medium). Frosted glass from Hyprland's "glass-nothing-widgets"
# layer rule; everything else is drawn here with cairo + Pango.
SMALL, GAP = 164, 12
MEDIUM = 2 * SMALL + GAP
FONT_UI, FONT_DISPLAY, FONT_ROUNDED = "SF Pro Text", "SF Pro Display", "SF Pro Rounded"
GLYPHS = "Symbols Nerd Font"
WHITE = (1, 1, 1, 1)


class Widget(Gtk.DrawingArea):
    RADIUS = 22

    def __init__(self, w, h):
        super().__init__()
        self.set_size_request(w, h)
        self.connect("draw", self._draw)

    def _draw(self, _w, cr):
        W, H = self.get_allocated_width(), self.get_allocated_height()
        self.background(cr, W, H)
        self.paint(cr, W, H)

    def background(self, cr, W, H):
        """Frosted glass card: translucent fill, hairline, light catching the top edge."""
        rounded_rect(cr, 0.5, 0.5, W - 1, H - 1, self.RADIUS)
        set_rgba(cr, COL["glass"])
        cr.fill_preserve()
        set_rgba(cr, COL["line"])
        cr.set_line_width(1)
        cr.stroke()
        hl = COL["highlight"]
        grad = cairo.LinearGradient(0, 0, 0, H * 0.45)
        grad.add_color_stop_rgba(0, hl[0], hl[1], hl[2], min(1, hl[3] * 2.2))
        grad.add_color_stop_rgba(1, hl[0], hl[1], hl[2], 0)
        rounded_rect(cr, 1.5, 1.5, W - 3, H - 3, self.RADIUS - 1)
        cr.set_source(grad)
        cr.stroke()

    def paint(self, cr, W, H):
        pass


# condition → (sky gradient day, sky gradient night, icon layers [(glyph, colour, dx, dy, scale)])
SUN, MOON, CLOUD = "\U000f0599", "\U000f0594", "\U000f0590"
SKIES = {
    "clear":   (("#2f7fdf", "#5fb0f0"), ("#0d1838", "#26386a")),
    "partly":  (("#3d82d6", "#78aee6"), ("#16213f", "#334468")),
    "cloudy":  (("#5d7591", "#8ea2b8"), ("#262e3c", "#424c5e")),
    "fog":     (("#7f8b98", "#a9b3bd"), ("#2b3038", "#474e58")),
    "rain":    (("#3f5168", "#6a7e95"), ("#1b2230", "#343f52")),
    "snow":    (("#7d97b8", "#b4c6dc"), ("#28344a", "#47566e")),
    "thunder": (("#33375a", "#5c5f86"), ("#191b30", "#33365a")),
}
CONDITION = {"113": "clear", "116": "partly", "119": "cloudy", "122": "cloudy",
             "143": "fog", "248": "fog", "260": "fog",
             "200": "thunder", "386": "thunder", "389": "thunder", "392": "thunder", "395": "thunder"}
for _c in ("179", "182", "185", "227", "230", "323", "326", "329", "332", "335", "338", "368", "371"):
    CONDITION[_c] = "snow"


def weather_kind(code):
    return CONDITION.get(code, "rain" if code in WEATHER_ICONS else "cloudy")


class WeatherWidget(Widget):
    """Apple Weather style: sky gradient for the current condition, white type."""

    def paint(self, cr, W, H):
        w = weather()
        kind = weather_kind(w["code"]) if w else "cloudy"
        day = w["is_day"] if w else True
        top, bottom = SKIES[kind][0 if day else 1]
        grad = cairo.LinearGradient(0, 0, 0, H)
        grad.add_color_stop_rgb(0, *rgb(top))
        grad.add_color_stop_rgb(1, *rgb(bottom))
        rounded_rect(cr, 0, 0, W, H, self.RADIUS)
        cr.set_source(grad)
        cr.fill()
        x = 16
        draw_text(cr, (w["area"] if w else "Weather") + " \U000f05cd", f"{FONT_UI} Semi-Bold 13", x, 14, WHITE, width=W - 28)
        draw_text(cr, w["temp"] if w else "--°", f"{FONT_DISPLAY} Light 44", x - 2, 30, WHITE)
        # colourful condition icon
        sun = (1.0, 0.84, 0.04, 1)
        layers = {
            "clear":  [(SUN if day else MOON, sun if day else (0.93, 0.93, 1, 1), 0, 0, 1)],
            "partly": [(SUN if day else MOON, sun if day else (0.93, 0.93, 1, 1), -6, -5, 0.8), (CLOUD, WHITE, 3, 2, 1)],
        }.get(kind, [(w["icon"] if w else CLOUD, WHITE, 0, 0, 1)])
        for glyph, color, dx, dy, sc in layers:
            draw_text(cr, glyph, f"{GLYPHS} {int(17 * sc)}", x + dx + 2, H - 64 + dy, color)
        draw_text(cr, w["cond"] if w else "Unavailable", f"{FONT_UI} Semi-Bold 12", x, H - 42, WHITE, width=W - 28)
        draw_text(cr, f"H:{w['hi']}  L:{w['lo']}" if w else "", f"{FONT_UI} Medium 12", x, H - 25, WHITE, alpha=0.85)


class ClockWidget(Widget):
    """Analog clock face like the macOS Clock widget; orange second hand."""

    def paint(self, cr, W, H):
        cx, cy, r = W / 2, H / 2, min(W, H) / 2 - 12
        dark = COL["dark"]
        face = (0.11, 0.11, 0.12, 0.92) if dark else (1, 1, 1, 0.95)
        ink = COL["fg"]
        cr.arc(cx, cy, r, 0, 2 * math.pi)
        set_rgba(cr, face)
        cr.fill()
        for i in range(1, 13):
            a = i * math.pi / 6 - math.pi / 2
            draw_text(cr, str(i), f"{FONT_ROUNDED} Medium 11", cx + math.cos(a) * (r - 14),
                      cy + math.sin(a) * (r - 14) - 8, ink, "center")
        for i in range(60):
            if i % 5:
                a = i * math.pi / 30
                cr.move_to(cx + math.cos(a) * (r - 3), cy + math.sin(a) * (r - 3))
                cr.line_to(cx + math.cos(a) * (r - 6), cy + math.sin(a) * (r - 6))
        set_rgba(cr, ink, 0.3)
        cr.set_line_width(1)
        cr.stroke()
        t = time.localtime()
        sec = t.tm_sec
        mins = t.tm_min + sec / 60
        hrs = t.tm_hour % 12 + mins / 60
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        for frac, length, width in ((hrs / 12, r * 0.5, 4.5), (mins / 60, r * 0.78, 3.5)):
            a = frac * 2 * math.pi - math.pi / 2
            cr.move_to(cx, cy)
            cr.line_to(cx + math.cos(a) * length, cy + math.sin(a) * length)
            set_rgba(cr, ink)
            cr.set_line_width(width)
            cr.stroke()
        a = sec / 60 * 2 * math.pi - math.pi / 2
        cr.move_to(cx - math.cos(a) * 12, cy - math.sin(a) * 12)
        cr.line_to(cx + math.cos(a) * (r - 6), cy + math.sin(a) * (r - 6))
        set_rgba(cr, COL["orange"])
        cr.set_line_width(1.5)
        cr.stroke()
        cr.arc(cx, cy, 3.2, 0, 2 * math.pi)
        cr.fill()
        cr.arc(cx, cy, 1.4, 0, 2 * math.pi)
        set_rgba(cr, face)
        cr.fill()


class CalendarWidget(Widget):
    """macOS Calendar widget (medium): weekday in red, big date, month grid."""

    def paint(self, cr, W, H):
        t = time.localtime()
        red, fg, dim = COL["red"], COL["fg"], COL["dim"]
        draw_text(cr, DAY_NAMES[t.tm_wday].upper(), f"{FONT_UI} Bold 11", 18, 16, red)
        draw_text(cr, str(t.tm_mday), f"{FONT_DISPLAY} Regular 52", 15, 28, fg)
        draw_text(cr, MONTH_NAMES[t.tm_mon - 1], f"{FONT_UI} Semi-Bold 13", 18, 96, fg)
        draw_text(cr, "No events today", f"{FONT_UI} Medium 11", 18, 116, dim)
        # month grid, weeks start on Monday
        gx, gy, cw, ch = 150, 16, (W - 150 - 14) / 7, 18
        draw_text(cr, MONTH_NAMES[t.tm_mon - 1].upper(), f"{FONT_UI} Bold 10", gx + 4, gy, red)
        for i, d in enumerate("MTWTFSS"):
            draw_text(cr, d, f"{FONT_UI} Semi-Bold 9", gx + cw * (i + 0.5), gy + 18, dim, "center")
        first = time.mktime((t.tm_year, t.tm_mon, 1, 12, 0, 0, 0, 0, -1))
        lead = time.localtime(first).tm_wday
        nxt = (t.tm_year + (t.tm_mon == 12), t.tm_mon % 12 + 1, 1, 12, 0, 0, 0, 0, -1)
        ndays = time.localtime(time.mktime(nxt) - 86400).tm_mday
        for day in range(1, ndays + 1):
            pos = lead + day - 1
            x, y = gx + cw * (pos % 7 + 0.5), gy + 34 + ch * (pos // 7)
            if day == t.tm_mday:
                cr.arc(x, y + 7, 8.5, 0, 2 * math.pi)
                set_rgba(cr, red)
                cr.fill()
                draw_text(cr, str(day), f"{FONT_UI} Bold 10", x, y, WHITE, "center")
            else:
                weekend = pos % 7 >= 5
                draw_text(cr, str(day), f"{FONT_UI} Medium 10", x, y, dim if weekend else fg, "center")


class StatsWidget(Widget):
    """System widget (medium): CPU / Memory / Disk as Activity-style rings + readouts."""

    RINGS = (("CPU", "pink"), ("Memory", "green"), ("Disk", "teal"))

    def __init__(self, shell, w, h):
        super().__init__(w, h)
        self.shell = shell

    def values(self):
        cpu = self.shell.cpu_last
        mem, used, total = Sys.mem()
        st = os.statvfs("/")
        disk = 100 * (1 - st.f_bavail / st.f_blocks) if st.f_blocks else 0
        return (cpu, mem, disk), (f"{cpu:.0f}%", f"{used:.1f} / {total:.0f} GB", f"{disk:.0f}%")

    def paint(self, cr, W, H):
        vals, texts = self.values()
        cx, cy = 18 + 62, H / 2
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        for i, ((_, color), v) in enumerate(zip(self.RINGS, vals)):
            r, c = 58 - i * 17, COL[color]
            cr.set_line_width(13)
            cr.arc(cx, cy, r, 0, 2 * math.pi)
            set_rgba(cr, c, 0.22)
            cr.stroke()
            if v > 0.5:
                cr.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * min(v, 100) / 100)
                set_rgba(cr, c)
                cr.stroke()
        x = 166
        for i, ((name, color), txt) in enumerate(zip(self.RINGS, texts)):
            y = 16 + i * 46
            draw_text(cr, name, f"{FONT_UI} Semi-Bold 11", x, y, COL[color])
            draw_text(cr, txt, f"{FONT_ROUNDED} Semi-Bold 17", x, y + 14, COL["fg"], width=W - x - 64)
        # thermals: a quiet column on the right
        for i, (k, v) in enumerate(Sys.temps().items()):
            y = 16 + i * 46
            draw_text(cr, k, f"{FONT_UI} Semi-Bold 11", W - 16, y, COL["dim"], "right")
            draw_text(cr, f"{v:.0f}°", f"{FONT_ROUNDED} Medium 15", W - 16, y + 15,
                      COL["orange"] if v >= 80 else COL["fg"], "right")


class Widgets(LayerWindow):
    def __init__(self, shell):
        E = GtkLayerShell.Edge
        super().__init__("nothing-widgets", [E.TOP, E.LEFT], {E.TOP: 56, E.LEFT: 18},
                         layer=GtkLayerShell.Layer.BOTTOM)
        self.shell = shell
        grid = box(vertical=True, spacing=GAP)
        row = box(spacing=GAP)
        self.weather = WeatherWidget(SMALL, SMALL)
        self.clock = ClockWidget(SMALL, SMALL)
        row.pack_start(self.weather, False, False, 0)
        row.pack_start(self.clock, False, False, 0)
        grid.pack_start(row, False, False, 0)
        self.calendar = CalendarWidget(MEDIUM, SMALL)
        grid.pack_start(self.calendar, False, False, 0)
        self.stats = StatsWidget(shell, MEDIUM, SMALL)
        grid.pack_start(self.stats, False, False, 0)
        self.add(grid)
        self.show_all()
        GLib.timeout_add(1000, self._tick)
        self._n = 0

    def _tick(self):
        self._n += 1
        self.clock.queue_draw()
        if self._n % 3 == 0:
            self.stats.queue_draw()
        if self._n % 60 == 0:
            self.calendar.queue_draw()
            self.weather.queue_draw()
        return True


# ═════════════════════════════ SHELL ═════════════════════════════
class Shell:
    def __init__(self):
        self.island = None
        self.control = None
        self.notifs = None
        self.cpu_hist = [0.0] * 40
        self.cpu_last = 0.0
        self._load_css()
        self.media = Media(self)
        self.notifs = NotifyLog(self)
        self.island = Island(self)
        self.control = Control(self)
        self.widgets = Widgets(self)
        self.media.refresh()
        self._workspaces()
        self._listen_hyprland()
        self._serve()
        Sys.cpu()
        GLib.timeout_add(1500, self._sample)
        GLib.timeout_add_seconds(5, self._compact_tick)
        GLib.timeout_add_seconds(900, self._weather_tick)
        GLib.timeout_add_seconds(2, self._night_start)
        GLib.timeout_add_seconds(60, self._night_tick)
        self._weather_tick()

    def _load_css(self):
        self.css = Gtk.CssProvider()
        try:
            self.css.load_from_path(CSS_FILE)
        except GLib.Error as e:
            print("css:", e.message, file=sys.stderr)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), self.css,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def reload_css(self):
        """style.css + palette (after `nothing-theme`): GTK restyles itself, cairo needs a redraw."""
        load_colors()
        try:
            self.css.load_from_path(CSS_FILE)
        except GLib.Error as e:
            return "css error: " + e.message
        for w in (self.island, self.control, self.widgets):
            w.queue_draw()
        if self.control.open:
            self.control.refresh()
        return "ok"

    def _sample(self):
        self.cpu_last = Sys.cpu()
        self.cpu_hist = (self.cpu_hist + [self.cpu_last])[-40:]
        return True

    def _compact_tick(self):
        self.island.refresh_compact()
        return True

    def _night_start(self):
        in_thread(lambda: run([os.path.join(BIN, "nothing-night"), "apply"], 10), lambda _r: self.night_changed())
        return False

    def _night_tick(self):
        in_thread(lambda: run([os.path.join(BIN, "nothing-night"), "tick"], 10))
        return True

    def night_changed(self):
        self.island.refresh_compact()
        if self.control.open:
            self.control.refresh()

    def _weather_tick(self):
        if os.path.exists(WEATHER_SCRIPT):
            in_thread(lambda: run([WEATHER_SCRIPT, "bar"], timeout=15),
                      lambda _r: (self.island.refresh_compact(), self.widgets.weather.queue_draw()))
        return True

    # ── toggles shared by island and control center ──
    def toggle(self, key, origin=None):
        def work():
            if key == "wifi":
                run(["nmcli", "radio", "wifi", "off" if Sys.wifi_on() else "on"], 5)
            elif key == "bt":
                if not Sys.bt_available():
                    spawn(["notify-send", "-a", "Bluetooth", "Bluetooth service is off",
                           "Enable it with: sudo systemctl enable --now bluetooth"])
                    return
                run(["bluetoothctl", "power", "off" if Sys.bt_on() else "on"], 5)
            elif key == "dnd":
                run(["swaync-client", "-d"])
                spawn("pkill -RTMIN+9 waybar")
            elif key == "night":
                run([os.path.join(BIN, "nothing-night"), "toggle"], 5)
            elif key == "mic":
                run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])
            elif key == "dark":
                run([os.path.join(BIN, "nothing-theme"), "toggle"], 15)

        def done(_):
            if self.control.open:
                self.control.refresh()
            if self.island.expanded:
                self.island.refresh_panel()
        in_thread(work, done)

    # ── hyprland ──
    def _workspaces(self):
        def fetch():
            return hyprctl_json("workspaces") or [], hyprctl_json("monitors") or []

        def apply(res):
            wss, mons = res
            mon = next((m for m in mons if m.get("name") == OUTPUT), mons[0] if mons else None)
            active = mon["activeWorkspace"]["id"] if mon else 1
            occupied = {w["id"] for w in wss if w.get("windows", 0) > 0}
            self.island.set_workspaces(active, occupied)
            fullscreen = any(w["id"] == active and w.get("hasfullscreen") for w in wss)
            if fullscreen and self.island.get_visible():
                self.island.collapse(force=True)
                self.island.hide()
            elif not fullscreen and not self.island.get_visible():
                self.island.show()
        in_thread(fetch, apply)

    def _listen_hyprland(self):
        sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
        if not sig:
            return
        path = os.path.join(RUNTIME, "hypr", sig, ".socket2.sock")
        interesting = ("workspace", "focusedmon", "openwindow", "closewindow", "movewindow",
                       "createworkspace", "destroyworkspace", "urgent", "fullscreen")

        def loop():
            while True:
                try:
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.connect(path)
                    buf = b""
                    while True:
                        data = s.recv(4096)
                        if not data:
                            break
                        buf += data
                        *lines, buf = buf.split(b"\n")
                        if any(l.split(b">>")[0].decode(errors="ignore").startswith(interesting) for l in lines):
                            GLib.idle_add(lambda: (self._workspaces(), False)[1])
                except OSError:
                    pass
                time.sleep(2)
        threading.Thread(target=loop, daemon=True).start()

    # ── IPC ──
    def _serve(self):
        try:
            os.unlink(SOCK)
        except OSError:
            pass
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(SOCK)
        srv.listen(8)
        GLib.io_add_watch(srv.fileno(), GLib.IO_IN, self._accept, srv)

    def _accept(self, _fd, _cond, srv):
        conn, _ = srv.accept()
        try:
            conn.settimeout(1)
            data = b""
            while True:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                data += chunk
            reply = self.handle(data.decode().split())
            conn.sendall((reply or "").encode())
        except OSError:
            pass
        finally:
            conn.close()
        return True

    def handle(self, args):
        if not args:
            return ""
        cmd, how = args[0], (args[1] if len(args) > 1 else "toggle")
        if cmd == "ping":
            return "pong"
        if cmd == "island":
            self.island.toggle(how)
        elif cmd == "control":
            self.control.toggle(how)
        elif cmd == "notif-status":
            return self.notifs.status()
        elif cmd == "night-changed":
            GLib.idle_add(lambda: (self.night_changed(), False)[1])
        elif cmd == "notif-clear":
            self.notifs.clear()
        elif cmd == "debug":
            c = self.control
            return json.dumps({"open": c.open, "had_focus": c._had_focus,
                               "visible": c.get_visible(), "size": c.get_size()[:]})
        elif cmd == "reload-css":
            return self.reload_css()
        elif cmd == "quit":
            GLib.idle_add(Gtk.main_quit)
        else:
            return f"unknown command: {cmd}"
        return ""


def main():
    Shell()
    try:
        Gtk.main()
    finally:
        try:
            os.unlink(SOCK)
        except OSError:
            pass


if __name__ == "__main__":
    main()
