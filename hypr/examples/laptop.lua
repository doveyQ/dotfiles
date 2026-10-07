-- Example machine file: laptop / 2-in-1 convertible (written on an HP ENVY x360 15).
--   cp ~/.config/hypr/examples/laptop.lua ~/.config/hypr/hyprland.local.lua
-- then check the names below against `hyprctl monitors` and `hyprctl devices`.
-- The copy is git-ignored. Not a convertible? Delete the auto-rotate part.

local scripts = os.getenv("HOME") .. "/.config/hypr/scripts"
local panel   = "eDP-1"                              -- built-in screen
local touchpad     = "syna3290:01-06cb:cd4f-touchpad" -- `hyprctl devices` → mice
local tablet_switch = "HP WMI hotkeys"                -- `hyprctl devices` → switches

return {
    main = panel,
    monitors = {
        -- external screens fall through to the "preferred / auto" rule
        { output = panel, mode = "preferred", position = "0x0", scale = 1 },
    },
    workspace = function() return panel end,

    setup = function()
        hl.config({
            input = {
                touchpad    = { natural_scroll = true },
                touchdevice = { output = panel },    -- touchscreen and pen stay on the panel
                tablet      = { output = panel },
            },
            gestures = { workspace_swipe_touch = true }, -- 3-finger swipe on the touchscreen too
        })

        -- touchpad: libinput's adaptive acceleration (the global "flat" is meant for mice)
        hl.device({ name = touchpad, accel_profile = "adaptive" })

        -- auto-rotate only while folded into tablet mode (needs iio-sensor-proxy)
        hl.on("hyprland.start", function()
            hl.exec_cmd(scripts .. "/autorotate.sh daemon " .. panel)
        end)
        hl.bind("switch:on:"  .. tablet_switch, hl.dsp.exec_cmd(scripts .. "/autorotate.sh tablet on"),  { locked = true })
        hl.bind("switch:off:" .. tablet_switch, hl.dsp.exec_cmd(scripts .. "/autorotate.sh tablet off"), { locked = true })
    end,
}
