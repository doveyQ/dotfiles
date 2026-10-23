-- Copenhagen — warm-neutral Nordic palette for Hyprland (hex values match palette.css)
-- Loaded by hyprland.lua as `theme`; the modules in conf/ read colours and fonts from here.
return {
    name = "copenhagen",

    -- window edges: a hair of chalk, like macOS window outlines
    border_active   = "rgba(e9e4da2e)",
    border_inactive = "rgba(e9e4da12)",
    border_size     = 1,
    borderless      = false,   -- true → no outlines, depth from shadows alone

    -- soft, warm, diffused depth (0xAARRGGBB)
    shadow          = 0x59100d0b,
    shadow_inactive = 0x33100d0b,

    glow            = "rgba(9dad9433)",   -- optional focus halo (Settings → Appearance)
    background      = "rgba(1e1c1aff)",   -- shows only where no wallpaper is drawn
    groupbar_active   = "rgba(9dad94cc)",
    groupbar_inactive = "rgba(6e696188)",

    fonts = {
        ui      = "SF Pro Text",      -- fontconfig falls back to Inter, then Cantarell
        display = "SF Pro Display",
        mono    = "SF Mono",          -- → JetBrains Mono
    },
}
