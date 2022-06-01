from enum import Enum
import inspect
import sys
sys.path.append("../lib")
from keymap import keymap, bindmap

Δ, λ = bindmap, keymap

class conf_gen(Enum):
    M1, M4 = 'Mod1', 'Mod4'
    Sh, Ct = 'Shift', 'Control'
    Font = 'Iosevka Bold 12'

    plain = inspect.cleandoc(f'''
        floating_modifier {M4}
        focus_follows_mouse no
        default_border normal
        default_floating_border normal
        font pango: {Font}
        hide_edge_borders both

        set  $bg     #000000ee
        set  $fg     #899CA1
        set  $fb     #005faf
        set  $ib     #285981
        set  $ub     #2E2457
        set  $blue   #285981
        set  $actbr  #020204

        client.focused           $fb     $bg    $fg    $bg  $actbr
        client.focused_inactive  $ib     $bg    $fg    $bg  $bg
        client.placeholder       $bg     $bg    $fg    $bg  $bg
        client.unfocused         $bg     $bg    $blue  $bg  $bg
        client.urgent            $bg     $ub    $fg    $ub  $ib

        client.background        $bg
        '''
    )

    exec = (
        'dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY SWAYSOCK',
        'systemctl --user start --no-block i3-session.target'
    )
    exec_always = ('systemctl --user restart --no-block negwm.service',)

    rules = inspect.cleandoc(f'''
        for_window [class=".*"] title_format "<span foreground=\'#395573\'> >_ </span> %title", border pixel 2
        for_window [class="^(inkscape|gimp)$"] move workspace $draw
        for_window [class="(?i)(?:steam|qt5ct|gcolor3|rdesktop|openssh-askpass|pavucontrol-qt|lutris|steam_app_.*|mpv)"] floating enable
        for_window [title="(?i)(?:copying|alsamixer|deleting|moving|File Transfer.*)"] floating enable
        for_window [instance="^(gpartedbin|recoll)$"] move workspace $sys, floating enable, focus
        for_window [title="Firefox — Sharing Indicator"] border pixel 1, sticky enable, move position 20 ppt -5 px
        for_window [title="i3_help"] floating enable sticky enable border normal
        no_focus [class="zoom" instance="zoom" title="^zoom$"]
        no_focus [title="Firefox — Sharing Indicator"]
        no_focus [window_type="splash"]
        '''
    )

    workspaces = [
        '︁ α:term',
        ' β:web',
        ' δ:dev',
        ' γ:doc',
        ' ζ:draw',
        ' ε:gfx',
        '@ ρ:obs',
        ' ξ:pic',
        ' ι:steam',
        ' η:sys',
        ' λ:vm',
        ' μ:wine'
    ]

    mode_default = Δ([
        λ({
            (f'{M4}+4') : '~/bin/screenshot',
            (f'{M4}+{Ct}+4') : '~/bin/screenshot -r',
            (f'{M4}+{Sh}+4') : 'flameshot gui',
        }, fmt='exec {cmd}'),

        λ({
            (f'{M1}+grave') : 'rofi -show run -show-icons -disable-history -theme neg',
            (f'{M4}+8') : 'playerctl volume 0.0 || amixer -q set Master 0 mute',
            (f'{M4}+c') : '~/bin/clip',
            (f'{M4}+g') : '~/bin/g',
            (f'{M4}+m') : '~/bin/music-rename current',
            (f'{M4}+p') : '~/bin/rofi-tmux-urls',
            (f'{M4}+{Sh}+6') : '~/bin/wl',
            (f'{M4}+{Sh}+8') : 'playerctl volume 1.0 || amixer -q set Master 65536 unmute',
            (f'{M4}+{Sh}+9') : 'dunstctl history-pop',
            (f'{M4}+{Sh}+l') : '~/bin/rofi-lutris',
            (f'{M4}+{Sh}+m') : '~/bin/rofi-audio',
            (f'{M4}+{Sh}+y') : '~/bin/clip youtube-dw-list',
            (f'{M4}+space') : 'dunstctl close-all',
            ('XF86Sleep') : 'systemctl suspend',
        }, fmt='exec --no-startup-id {cmd}'),

        λ({
            (f'{M4}+j') : 'down',
            (f'{M4}+h') : 'left',
            (f'{M4}+l') : 'right',
            (f'{M4}+k') : 'up',
        }, fmt='focus {cmd}'),

        λ({
            (f'{M4}+apostrophe') : 'reload',
            (f'{M4}+{Sh}+apostrophe') : 'restart'
        }),

        λ({
            (f'{M4}+grave') : 'focus_next_visible',
            (f'{M4}+{Sh}+grave') : 'focus_prev_visible',
            (f'{M1}+Tab'): 'switch',
            (f'{M4}+slash') : 'switch',
        }, fmt='$remember_focused {cmd}'),

        λ({
            (f'{M4}+{Ct}+a') : 'dialog',
            (f'{M4}+{Ct}+s') : 'geom_dump',
            (f'{M4}+{Ct}+space') : 'geom_restore',
            (f'{M4}+s') : 'hide_current',
            (f'{M4}+3') : 'next',
        }, fmt='$scratchpad {cmd}'),

        λ({
            (f'{M4}+period') : 'next',
            (f'{M4}+{Sh}+2') : 'play-pause',
            (f'{M4}+comma') : 'previous',
            ('XF86AudioLowerVolume') : 'volume 0.05- || playerctl volume 0.01-',
            ('XF86AudioRaiseVolume') : 'volume 0.05+ || playerctl volume 0.01+',
        }, fmt='exec --no-startup-id playerctl {cmd}'),

        λ({
            ('XF86AudioNext') : 'next',
            ('XF86AudioPlay') : 'play',
            ('XF86AudioPrev') : 'previous',
            ('XF86AudioStop') : 'stop',
        }, fmt='exec --no-startup-id playerctl {cmd}'),

        λ({
            (f'{M4}+{Sh}+a') : 'attach',
            (f'{M4}+{Sh}+s') : 'autoprop',
            (f'{M4}+{Ct}+grave') : 'cmd_menu',
            (f'{M1}+g') : 'goto_win',
            (f'{M4}+{Ct}+g') : 'movews',
            (f'{M1}+{Ct}+g') : 'ws',
        }, fmt='$menu {cmd}'),

        λ({
            (f'{M4}+q') : 'fullscreen toggle',
            (f'{M4}+{Ct}+q') : 'kill',
        }),
    ])

    mode_resize = Δ([
        λ({
            'bottom' : ['j', 's'],
            'left' : ['h', 'a'],
            'right' : ['l', 'd'],
            'top' : ['k', 'w'],
        }, fmt='$actions resize {cmd} 4'),

        λ({
            'bottom' : [f'{Sh}+j', f'{Sh}+s'],
            'left' : [f'{Sh}+h', f'{Sh}+a'],
            'right' : [f'{Sh}+l', f'{Sh}+d'],
            'top' : [f'{Sh}+k', f'{Sh}+w'],
        }, fmt='$actions resize {cmd} -4'),
        ], bind=f'{M4}+r'
     )

    mode_spec = Δ([
        λ({
            ('e') : '[urgent=latest] focus',
            ('l') : 'exec i3lockr -p 8 ',
            (f'{Sh}+d') : 'floating toggle',
        }, exit=True),

        λ({
            (f'{Sh}+t') : 'gtk_theme',
            (f'{Sh}+i') : 'icon_theme',
            ('i') : 'pulse_input',
            ('o') : 'pulse_output',
            ('m') : 'xprop_show',
        }, fmt='$menu {cmd}', exit=True),
        ], bind=f'{M1}+e'
    )

    mode_wm = Δ([
        λ({
            (f'grave') : 'default',
            (f'minus') : 'splith',
            (f'backslash') : 'splitv',
            (f't') : 'tabbed',
            (f'{Ct}+t') : 'toggle',
        }, fmt='layout {cmd}', exit=True),

        λ({
            'horizontal' : ['h', 'l'],
            'vertical' : ['j', 'k'],
        }, fmt='split', exit=True),

        λ({
            ('w') : 'top',
            ('a') : 'left',
            ('s') : 'bottom',
            ('d') : 'right',
        }, fmt='move {cmd}'),

        λ({
            (f'{Sh}+plus') : 'grow',
            ('x') : 'maxhor',
            ('m') : 'maximize',
            ('y') : 'maxvert',
            ('c') : 'none',
            (f'{Sh}+c') : 'resize',
            'revert_maximize' : [f'{Sh}+m', f'{Sh}+x', f'{Sh}+y'],
            'shrink' : [f'{Sh}+minus'],
        }, fmt='$actions'),

        λ({
            'hdown' : [f'{Sh}+w'],
            'hup' : [f'{Sh}+a'],
            'vleft' : [f'{Sh}+s'],
            'vright' : [f'{Sh}+d'],
        }, fmt='$actions {cmd} x2'),
        ], bind=f'{M4}+minus'
    )
