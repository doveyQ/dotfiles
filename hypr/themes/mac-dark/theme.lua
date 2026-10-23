-- macOS Dark — Hyprland colours (match palette.css). Loaded by hyprland.lua as `theme`.
return {
    name = "mac-dark",
    dark = true,

    -- hairline window edges, like macOS
    border_active   = "rgba(ffffff2e)",
    border_inactive = "rgba(ffffff14)",
    border_size     = 1,
    borderless      = false,   -- true → no outlines, depth from shadows alone

    shadow          = 0x50000000,
    shadow_inactive = 0x30000000,
    glow            = "rgba(0a84ff40)",   -- optional focus halo (Settings → Appearance)

    blur_brightness = 0.85,
    blur_vibrancy_darkness = 0.2,

    background        = "rgba(1e1e1eff)",
    titlebar          = "rgba(2c2c2ee6)",   -- hyprbars title bars (blurred)
    titlebar_text     = "rgba(e5e5eaff)",
    titlebar_button_inactive = "rgba(5a5a5eff)",
    groupbar_active   = "rgba(0a84ffcc)",
    groupbar_inactive = "rgba(63636688)",

    fonts = { ui = "SF Pro Text", display = "SF Pro Display", mono = "SF Mono" },
}
