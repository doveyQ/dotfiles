-- Look and feel: macOS-like depth — hairline edges, soft rounded corners, deep diffused
-- shadows, frosted glass.  Colours come from the theme (~/.config/hypr/theme/theme.lua).
return function(ctx)
    local t = ctx.theme
    local border = t.borderless and 0 or (t.border_size or 1)

    hl.config({
        general = {
            gaps_in     = 6,
            gaps_out    = 12,
            border_size = border,
            col = {
                active_border   = t.border_active,
                inactive_border = t.border_inactive,
            },
            resize_on_border = true,
            extend_border_grab_area = 12,   -- still easy to grab with a 1px / no border
            allow_tearing    = false,
            layout           = "dwindle",
        },

        decoration = {
            rounding       = 14,
            rounding_power = 3.0,   -- continuous-curve corners, like macOS windows
            active_opacity   = 1.0,
            inactive_opacity = 0.96,
            dim_special      = 0.3,

            shadow = {
                enabled        = true,
                range          = 28,
                render_power   = 2,      -- low power = wide, soft falloff
                offset         = "0 8",  -- light from above
                color          = t.shadow,
                color_inactive = t.shadow_inactive,
            },

            -- off by default; Settings → Appearance → Soft glow turns it on
            glow = {
                enabled        = false,
                range          = 12,
                render_power   = 3,
                color          = t.glow,
                color_inactive = "rgba(00000000)",
            },

            blur = {
                enabled           = true,
                size              = 6,
                passes            = 3,
                noise             = 0.015,
                contrast          = 0.95,
                brightness        = 0.9,
                vibrancy          = 0.12,  -- a little colour through the glass
                popups            = true,
                new_optimizations = true,
            },
        },

        group = {
            col = {
                border_active   = t.border_active,
                border_inactive = t.border_inactive,
            },
            groupbar = {
                font_family  = t.fonts.ui,
                font_size    = 11,
                height       = 18,
                rounding     = 6,
                gradients    = true,
                col = { active = t.groupbar_active, inactive = t.groupbar_inactive },
            },
        },

        animations = { enabled = true },
    })

    -- fluid: gentle ease-out + a soft spring for windows
    hl.curve("fluid",  { type = "bezier", points = { {0.22, 1}, {0.36, 1} } })
    hl.curve("linear", { type = "bezier", points = { {0, 0}, {1, 1} } })
    hl.curve("soft",   { type = "spring", mass = 1, stiffness = 210, dampening = 26 })

    hl.animation({ leaf = "global",     enabled = true, speed = 8,   bezier = "default" })
    hl.animation({ leaf = "border",     enabled = true, speed = 5,   bezier = "fluid" })
    hl.animation({ leaf = "windows",    enabled = true, speed = 4.5, spring = "soft" })
    hl.animation({ leaf = "windowsIn",  enabled = true, speed = 4,   spring = "soft", style = "popin 92%" })
    hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.8, bezier = "linear", style = "popin 92%" })
    hl.animation({ leaf = "fade",       enabled = true, speed = 3,   bezier = "fluid" })
    hl.animation({ leaf = "layersIn",   enabled = true, speed = 3.5, bezier = "fluid", style = "slide top" })
    hl.animation({ leaf = "layersOut",  enabled = true, speed = 1.6, bezier = "linear", style = "fade" })
    hl.animation({ leaf = "fadeLayersIn",  enabled = true, speed = 2.5, bezier = "fluid" })
    hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.8, bezier = "linear" })
    hl.animation({ leaf = "workspaces", enabled = true, speed = 3.5, bezier = "fluid", style = "slide" })
    hl.animation({ leaf = "specialWorkspace", enabled = true, speed = 3, bezier = "fluid", style = "slidevert" })

    hl.config({
        dwindle = { preserve_split = true },
        master  = { new_status = "master" },
        misc = {
            force_default_wallpaper  = 0,
            disable_hyprland_logo    = true,
            disable_splash_rendering = true,
            background_color         = t.background,
            font_family              = t.fonts.ui,
            vrr                      = 2,
            focus_on_activate        = true,
            key_press_enables_dpms   = true,
            mouse_move_enables_dpms  = true,
            allow_session_lock_restore = true,  -- if hyprlock ever crashes, a new one can take over
        },
        binds = {
            workspace_back_and_forth = false,
            allow_workspace_cycles   = true,
        },
        cursor = {
            default_monitor = ctx.machine.main,   -- nil → Hyprland's default
        },
        render = {
            direct_scanout = 2, -- games only, safe on AMD
        },
        ecosystem = {
            no_update_news  = true,
            no_donation_nag = true,
        },
    })
end
