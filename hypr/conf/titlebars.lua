-- macOS title bars with traffic lights (close · minimise · zoom) for windows that don't draw
-- their own — kitty, Dolphin, … — through Hyprland's official hyprbars plugin.
--   install:  yay -S hyprland-plugin-hyprbars       (built from github.com/hyprwm/hyprland-plugins)
-- Without the plugin this module does nothing. Apps with their own header bar (GTK / libadwaita,
-- browsers, VS Code, the Settings app) get no second bar; their traffic lights come from
-- hypr/themes/gtk3.css / gtk4.css or the app itself.
local PLUGIN = "/usr/lib/libhyprbars.so"

-- apps that already draw window controls in their own title / tab bar
local OWN_CONTROLS = "^(firefox|librewolf|chromium|google-chrome|brave-browser|code|Code|code-oss|"
    .. "org\\.gnome\\..*|nautilus|zenity|org\\.pulseaudio\\.pavucontrol|dev\\.nothing\\.Settings|"
    .. "nothing-settings|steam|Steam|discord|vesktop|obsidian|Spotify|spotify)$"

local function dispatch(lua) return "hyprctl dispatch '" .. lua .. "'" end

return function(ctx)
    local f = io.open(PLUGIN)
    if not f then return end
    f:close()

    local loaded = false
    for _, p in ipairs(hl.get_loaded_plugins() or {}) do
        if p.name and p.name:lower():find("hyprbars", 1, true) then loaded = true end
    end
    if not loaded then hl.plugin.load(PLUGIN) end            -- once; reloads keep it
    if not (hl.plugin.hyprbars and hl.plugin.hyprbars.add_button) then return end

    local t = ctx.theme
    local zoom = dispatch('hl.dsp.window.fullscreen({ mode = "maximized" })')
    hl.config({
        plugin = {
            hyprbars = {
                bar_height                 = 28,
                bar_color                  = t.titlebar,
                ["col.text"]               = t.titlebar_text,
                bar_blur                   = true,
                bar_title_enabled          = true,
                bar_text_font              = t.fonts.ui,
                bar_text_size              = 11,
                bar_text_weight            = "semibold",
                bar_text_align             = "center",
                bar_buttons_alignment      = "left",         -- macOS: lights on the left
                bar_padding                = 12,
                bar_button_padding         = 8,
                bar_part_of_window         = true,
                bar_precedence_over_border = true,
                icon_on_hover              = true,           -- ×  −  + appear on hover
                inactive_button_color      = t.titlebar_button_inactive,
                on_double_click            = zoom,
            },
        },
    })
    -- left alignment: first added = leftmost  →  close, minimise, zoom
    local glyph = "rgba(4d0000b3)"
    hl.plugin.hyprbars.add_button({ bg_color = "rgb(ff5f56)", fg_color = glyph, size = 12, icon = "×",
        action = dispatch("hl.dsp.window.close()") })
    hl.plugin.hyprbars.add_button({ bg_color = "rgb(ffbd2e)", fg_color = glyph, size = 12, icon = "−",
        action = dispatch('hl.dsp.window.move({ workspace = "special:magic", follow = false })') })   -- Super+S
    hl.plugin.hyprbars.add_button({ bg_color = "rgb(27c93f)", fg_color = glyph, size = 12, icon = "+",
        action = zoom })

    hl.window_rule({ name = "hyprbars-own-controls", match = { class = OWN_CONTROLS }, ["hyprbars:no_bar"] = true })
    hl.window_rule({ name = "hyprbars-fullscreen",   match = { fullscreen = true },     ["hyprbars:no_bar"] = true })
end
