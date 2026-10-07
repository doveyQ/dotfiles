-- Example machine file: two monitors stacked vertically.
--   cp ~/.config/hypr/examples/desktop-dual-monitor.lua ~/.config/hypr/hyprland.local.lua
-- then adjust names / modes (`hyprctl monitors`). The copy is git-ignored.
-- For Waybar on the main screen only, see waybar/local.example.jsonc.

local top, main = "HDMI-A-1", "DP-2"

return {
    main = main,                -- island, bar, dock, popups, recorder
    monitors = {
        { output = top,  mode = "1920x1080@70",  position = "0x0",    scale = 1 },
        { output = main, mode = "1920x1080@144", position = "0x1080", scale = 1, vrr = 2 }, -- VRR in fullscreen only
    },
    -- 1-5 → main (bottom) · 6-10 → top
    workspace = function(i) return (i <= 5) and main or top end,

    setup = function()
        hl.env("NOTHING_WORKSPACES", "5")   -- the island shows dots for the main screen's 1-5
    end,
}
