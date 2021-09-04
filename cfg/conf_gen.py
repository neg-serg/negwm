from enum import Enum

class conf_gen(Enum):
    actions_wm = dict(
        keymap = dict(
            grow = ['Shift+plus'],
            maxhor = ['x'],
            maximize = ['m'],
            maxvert = ['y'],
            none = ['c'],
            resize = ['Shift+c'],
            revert_maximize = ['Shift+m', 'Shift+x', 'Shift+y'],
            shrink = ['Shift+minus']
        )
    )

    bind_modes = dict(
        default = '',
        resize = 'Mod4+r',
        spec = 'Mod1+e',
        wm = 'Mod4+minus'
    )

    colors = dict(
        background = ['#000000ee'],
        focused = ['#000011dd', '#000000ee', '#ddddee', '#112211', '#0C0C0D'],
        focused_inactive = ['#000000dd', '#000000ee', '#005fff', '#000000', '#020204'],
        placeholder = ['#000000ee', '#000000', '#ffffff', '#000000', '#0c0c0c'],
        unfocused = ['#000000ee', '#000000', '#315c70', '#000000', '#020204'],
        urgent = ['#000000ee', '#2E2457', '#4C407C', '#32275E', '#32275E']
    )

    exec = {
        'no_startup_id': {
            'Mod1+grave': 'rofi -show run -show-icons -disable-history -theme neg',
            'Mod4+8': 'playerctl volume 0.0 || amixer -q set Master 0 mute',
            'Mod4+Shift+6': '~/bin/wl',
            'Mod4+Shift+8': 'playerctl volume 1.0 || amixer -q set Master 65536 unmute',
            'Mod4+Shift+9': 'dunstctl history-pop',
            'Mod4+Shift+apostrophe': '${XDG_CONFIG_HOME}/negi3wm/bin/i3-restart',
            'Mod4+Shift+i': '~/bin/scripts/rofi-nm',
            'Mod4+Shift+l': '~/bin/scripts/rofi-lutris',
            'Mod4+Shift+m': '~/bin/scripts/rofi-audio',
            'Mod4+Shift+y': '~/bin/clip youtube-dw-list',
            'Mod4+apostrophe': '${XDG_CONFIG_HOME}/negi3wm/bin/i3-reload',
            'Mod4+c': '~/bin/clip',
            'Mod4+g': '~/bin/g',
            'Mod4+p': '~/bin/scripts/rofi-tmux-urls',
            'Mod4+space': 'dunstctl close-all',
            'XF86Sleep': 'sudo systemctl suspend'
        },
        'plain': {
            'Mod4+4': '~/bin/scripts/screenshot',
            'Mod4+Control+4': '~/bin/scripts/screenshot -r',
            'Mod4+Shift+4': 'flameshot gui'
        }
    }

    focus = dict(
        keymap = dict(
            down = ['j'],
            left = ['h'],
            right = ['l'],
            up = ['k']
        ),
        modkey = 'Mod4'
    )

    layout_wm = dict(
        keymap = dict(
           default = ['grave'],
           splith = ['minus'],
           splitv = ['backslash'],
           tabbed = ['t'],
           toggle = ['Control+t'],
        )
    )

    main = dict(
        default_orientation = 'auto',
        floating_modifier = 'Mod4',
        focus_follows_mouse = 'no',
        focus_on_window_activation = 'smart',
        focus_wrapping = 'workspace',
        force_display_urgency_hint = '2000 ms',
        mouse_warping = 'none',
        workspace_layout = 'tabbed'
    )

    media = dict(
        keymap = {
            'next': ['XF86AudioNext', 'period'],
            'play': ['XF86AudioPlay'],
            'play-pause': ['Shift+2'],
            'previous': ['XF86AudioPrev', 'comma'],
            'stop': ['XF86AudioStop']
        },
        modkey = 'Mod4'
    )

    menu = dict(
        keymap = dict(
            attach = ['Mod4+Shift+a'],
            autoprop = ['Mod4+Shift+s'],
            cmd_menu = ['Mod4+Control+grave'],
            goto_win = ['Mod1+g'],
            movews = ['Mod4+Control+g'],
            ws = ['Mod1+Control+g']
        )
    )

    menu_spec = dict(
        keymap = dict(
            gtk_theme = ['Shift+t'],
            icon_theme = ['Shift+i'],
            pulse_input = ['i'],
            pulse_output = ['o'],
            xprop = ['m']
        )
    )

    misc = dict(
        keymap = {
            'fullscreen toggle': ['q'],
            'kill': ['Control+q']
        },
        modkey = 'Mod4'
    )

    misc_spec = dict(
        keymap = {
            '[urgent=latest] focus': ['e'],
            'floating toggle': ['Shift+d']
        }
    )

    move = dict(
        keymap = dict(
            bottom = ['s'],
            left = ['a'],
            right = ['d'],
            top = ['w']
        )
    )

    move_acts = dict(
        keymap = dict(
            hdown = ['Shift+w'],
            hup = ['Shift+a'],
            vleft = ['Shift+s'],
            vright = ['Shift+d']
        ),
        param = 'x2'
    )

    quad = dict(
        keymap = {
            '1' : '1',
            '2' : '2',
            '3' : '3',
            '4' : '4'
        }
    )

    remember_focused = dict(
        keymap = dict(
            focus_next_visible = ['Mod4+grave'],
            focus_prev_visible = ['Mod4+Shift+grave'],
            switch = ['Mod1+Tab', 'Mod4+slash']
        )
    )

    resize_minus = dict(
        keymap = dict(
            bottom = ['j', 's'],
            left = ['h', 'a'],
            right = ['l', 'd'],
            top = ['k', 'w']
        ),
        modkey = 'Shift',
        param = '-4'
    )

    resize_plus = dict(
        keymap = dict(
            bottom = ['j', 's'],
            left = ['h', 'a'],
            right = ['l', 'd'],
            top = ['k', 'w']
        ),
        param = '4'
    )

    rules = {
        '[class=".*"]': 'title_format "<span foreground=\'#395573\'> >_ </span> %title", border pixel 5',
        '[class="^(Gcolor3|rdesktop|openssh-askpass)$"]': 'floating enable',
        '[class="^(inkscape|gimp)$"]': 'move workspace $draw',
        '[class="^(steam|Steam)$"]': 'floating enable',
        '[class="steam_app_.*"]': 'floating enable',
        '[instance="^(gpartedbin|recoll)$"]': 'move workspace $sys, floating enable, focus'
    }

    scratchpad = dict(
        keymap = dict(
            dialog = ['Control+a'],
            geom_dump = ['Control+s'],
            geom_restore = ['Control+space'],
            hide_current = ['s'],
            next = ['3']
        ),
        modkey = 'Mod4'
    )

    split = dict(
        keymap = dict(
            horizontal = ['h', 'l'],
            vertical = ['j', 'k']
        )
    )

    startup = dict(
        always = dict(
            gnome_configs = '${XDG_CONFIG_HOME}/negi3wm/bin/gnome-conf',
            negi3wm = 'dash -c ${XDG_CONFIG_HOME}/negi3wm/bin/negi3wm_run',
            polybar = 'pkill -x polybar; [ $(pgrep -x polybar|wc -l) -le 1 ] && polybar -c ${XDG_CONFIG_HOME}/polybar/main main'
        ),
        once = {
            'dbus-env' : 'hash dbus-update-activation-environment 2>/dev/null && dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY SWAYSOCK',
            'gpaste' : '/usr/sbin/gpaste-client daemon',
            'gsd-xsettings' : '/usr/lib/gsd-xsettings',
            'polkit-gnome' : '/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1',
            'xiccd' : '/usr/bin/xiccd'
        }
   )

    theme = {
        'default_border' : 'normal',
        'default_floating_border' : 'normal',
        'font' : 'Iosevka 12',
        'hide_edge_borders' : 'both',
        'show_marks' : 'yes',
        'title_align' : 'center'
    }

    set_vars = dict(
        exit = 'mode \\"default\\"',
        i3 = '${XDG_CONFIG_HOME}/negi3wm'
    )

    vol = dict(
        keymap = dict(
            d = ['XF86AudioLowerVolume'],
            u = ['XF86AudioRaiseVolume']
        )
    )

    workspaces = dict(
        dev = '\ue267 δ:dev',
        doc = '\uf15c γ:doc',
        draw = '\uf03e ζ:draw',
        gfx = '\uf34c ε:gfx',
        obs = '@ ρ:obs',
        pic = '\uf03e ξ:pic',
        steam = '\uf1b7 ι:steam',
        sys = '\uf0ad η:sys',
        term = '\ue236︁ α:term',
        vm = '\uf1cd λ:vm',
        web = '\uf269 β:web',
        wine = '\uf1cb μ:wine'
    )
