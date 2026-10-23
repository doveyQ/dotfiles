-- ┏┳┓┏━┓┏━╸┏━┓┏━┓
-- ┃┃┃┣━┫┃  ┃ ┃┗━┓   macOS-style Hyprland — frosted glass, SF Pro, light & dark
-- ╹ ╹╹ ╹┗━╸┗━┛┗━┛   Hyprland 0.56+ (Lua config)
--
-- Hyprland ≥ 0.56 reads hyprland.lua (the old hyprland.conf syntax is gone).
-- Note: on 0.56 `hyprctl dispatch <name> <args>` no longer works — dispatchers are
-- Lua expressions:  hyprctl dispatch 'hl.dsp.exit()'
-- Wiki: https://wiki.hypr.land/Configuring/Start/
--
-- This file only loads things; the configuration lives in conf/:
--   monitors.lua   outputs + which monitor holds which workspace
--   autostart.lua  environment variables and everything started with the session
--   input.lua      keyboard, mouse, touchpad, gestures
--   look.lua       borders, rounding, shadows, blur, animations
--   rules.lua      window and layer rules
--   titlebars.lua  macOS title bars + traffic lights (hyprbars plugin, when installed)
--   keybinds.lua   programs and every key binding
-- Colours and fonts come from the active theme: ~/.config/hypr/theme → themes/mac-dark or
-- themes/mac-light (git-ignored link, switched by `nothing-theme toggle` / Super+Shift+T).

local home    = os.getenv("HOME")
local hypr    = home .. "/.config/hypr"

local function optional(file)   -- dofile, or nil when the file doesn't exist
    local f = io.open(file)
    if not f then return nil end
    f:close()
    return dofile(file)          -- no pcall: mistakes show up in the error bar
end

local ctx = {
    hypr    = hypr,
    bin     = home .. "/.local/bin",
    scripts = hypr .. "/scripts",
    theme   = optional(hypr .. "/theme/theme.lua") or dofile(hypr .. "/themes/mac-dark/theme.lua"),

    -- Everything specific to one computer lives in ~/.config/hypr/hyprland.local.lua
    -- (git-ignored — start from hypr/examples/). It returns a table, every field optional:
    --   main       output for the island, bar, dock, popups, recorder (→ $NOTHING_OUTPUT)
    --   monitors   list of hl.monitor() specs
    --   workspace  function(i) → output for workspace i
    --   setup      function, runs at the very end: devices, binds, autostart, overrides …
    -- Without it: every screen at its preferred mode, workspaces wherever they are opened.
    machine = optional(hypr .. "/hyprland.local.lua") or {},

    -- Choices made in the Settings app (Super+I) or `nothing-settings set …` are generated
    -- into ~/.config/nothing/settings.lua (outside the repo). They win over the machine file.
    ui      = optional(home .. "/.config/nothing/settings.lua") or {},
}
if ctx.ui.main then ctx.machine.main = ctx.ui.main end

for _, name in ipairs({ "monitors", "autostart", "input", "look", "rules", "titlebars", "keybinds" }) do
    dofile(hypr .. "/conf/" .. name .. ".lua")(ctx)
end

--------------------------------
---- MACHINE-LOCAL OVERRIDES ---
--------------------------------
-- hyprland.local.lua's setup() runs last, so it can override anything in conf/
if ctx.machine.setup then ctx.machine.setup() end

-- Settings app choices (keyboard, mouse, touchpad, gaps, blur …) are applied last
if ctx.ui.config then hl.config(ctx.ui.config) end
