from enum import Enum
import inspect
import sys
sys.path.append("../lib")
from lib.keymap import keymap, bindmap

Δ, λ = bindmap, keymap
M1, M4 = 'Mod1', 'Mod4'
Sh, Ct = 'Shift', 'Control'
Font = 'Iosevka Bold 12'
Exec = 'exec --no-startup-id'

def plain(): return inspect.cleandoc(f'''
    floating_modifier {M4}
    focus_follows_mouse no
    font pango: {Font}
    hide_edge_borders both

    set  $bg     #000000ee
    set  $fg     #899CA1
    set  $fb     #005faf
    set  $ib     #285981
    set  $ub     #2E2457
    set  $blue   #285981
    set  $actbr  #020204

    client.focused           $fb  $bg  $fg    $bg  $actbr
    client.focused_inactive  $ib  $bg  $fg    $bg  $bg
    client.placeholder       $bg  $bg  $fg    $bg  $bg
    client.unfocused         $bg  $bg  $blue  $bg  $bg
    client.urgent            $bg  $ub  $fg    $ub  $ib

    client.background        $bg
    '''
)

def exec(): return (
    'dbus-update-activation-environment --systemd DISPLAY WAYLAND_DISPLAY SWAYSOCK',
    'systemctl --user start --no-block i3-session.target'
)

def exec_always(): return (
    'systemctl --user restart --no-block negwm.service',
)

def rules(): return inspect.cleandoc(f'''
    for_window [class=".*"] title_format "<span foreground=\'#395573\'> >_ </span> %title", border pixel 2

    for_window [class="(?i)(alacr|k)itty"] border none
    for_window [class="(?i)\\.exe"] floating enable, border none, move position center
    for_window [class="^(inkscape|gimp)$"] move workspace $draw
    for_window [class="(?i)(?:steam|qt5ct|gcolor3|rdesktop|openssh-askpass|lutris|steam_app_.*|wine)"] floating enable
    for_window [class=zoom] border none
    for_window [class=zoom title="(?i)(participants|settings)"] floating enable
    for_window [instance="^(gpartedbin|recoll)$"] move workspace $sys, floating enable, focus
    for_window [title="Firefox — Sharing Indicator"] border pixel 1, sticky enable, move position 20 ppt -5 px
    for_window [title="(?i)(?:File Transfer.*)"] floating enable
    for_window [window_role="browser"] border none
    for_window [window_role="^(pop-up|task_dialog)$"] floating enable

    no_focus [title="Firefox — Sharing Indicator"]
    no_focus [window_type="splash"]
    '''
)

def workspaces():
    use_greek: bool = True
    use_runes: bool = False
    if use_greek:
        return [
            '︁ α:term', ' β:web', ' δ:dev',
            ' γ:doc', ' ζ:draw', '߷ θ:gfx',
            '✽ ρ:obs', ' ξ:pic', ' ι:steam',
            ' η:sys', ' λ:vm', ' μ:wine'
        ]
    if use_runes:
        return [
            '︁ ᚠ:term', ' ᚢ:web', ' ᚦ:dev',
            ' ᚨ:doc', ' ᚱ:draw', '߷ ᚲ:gfx',
            '✽ ᚷ:obs', ' ᚹ:pic', ' ᚺ:steam',
            ' ᚾ:sys', ' ᛁ:vm', ' ᛃ:wine'
        ]

def mode_default(): return Δ([
    λ({
        f'{M4}+4': '~/bin/screenshot',
        f'{M4}+{Ct}+4': '~/bin/screenshot -r',
        f'{M4}+{Sh}+4': 'flameshot gui',
    }, fmt='exec {cmd}'),
    λ({
        f'{M1}+grave': 'rofi -show run -show-icons -disable-history -theme neg',
        f'{M4}+c': '~/bin/clip',
        f'{M4}+m': 'zsh -c "~/bin/music-rename current"',
        f'{M4}+p': '~/bin/rofi-tmux-urls',
        f'{M4}+{Sh}+p': 'zsh -c /usr/bin/rofi-pass',
        f'{M4}+{Sh}+6': '~/bin/wl',
        f'{M4}+{Sh}+9': 'dunstctl history-pop',
        f'{M4}+{Sh}+l': '~/bin/rofi-lutris',
        f'{M4}+{Sh}+m': '~/bin/main-menu',
        f'{M4}+{Sh}+y': '~/bin/clip youtube-dw-list',
        f'{M4}+space': 'dunstctl close-all',
        'XF86Sleep': 'systemctl suspend',
        f'{M4}+8': '~/bin/pl vol mute',
        f'{M4}+{Sh}+8': '~/bin/pl vol unmute',
    }, fmt=f'{Exec} {{cmd}}'),
    λ({
        f'{M4}+j': 'down',
        f'{M4}+h': 'left',
        f'{M4}+l': 'right',
        f'{M4}+k': 'up',
        f'{M4}+7': 'parent',
        f'{M4}+2': 'child',
    }, fmt='focus {cmd}'),
    # move workspace to left and right monitors
    λ({
        f'{M4}+Shift+bracketleft': 'left',
        f'{M4}+Shift+bracketright': 'right',
    }, fmt='move workspace to output {cmd}'),
    λ({
        f'{M4}+apostrophe': f'reload; {Exec} systemctl --user restart negwm',
        f'{M4}+backslash': f'reload; {Exec} systemctl --user restart negwm; {Exec} polybar-msg cmd restart',
        f'{M4}+{Sh}+apostrophe': 'restart'
    }),
    λ({
        f'{M4}+grave': 'focus_next_visible',
        f'{M4}+{Sh}+grave': 'focus_prev_visible',
        f'{M1}+Tab': 'switch',
        f'{M4}+slash': 'switch',
    }, fmt='$remember_focused {cmd}'),
    λ({
        f'{M4}+{Ct}+a': 'dialog',
        f'{M4}+{Ct}+s': 'geom_dump',
        f'{M4}+{Ct}+space': 'geom_restore',
        f'{M4}+s': 'hide_current',
        f'{M4}+3': 'next',
    }, fmt='$scratchpad {cmd}'),
    λ({
        f'{M4}+period': 'cmd next',
        f'{M4}+{Sh}+2': 'cmd play-pause',
        f'{M4}+comma': 'cmd previous',
        'XF86AudioLowerVolume': 'vol down',
        'XF86AudioRaiseVolume': 'vol up',
    }, fmt=f'{Exec} ~/bin/pl {{cmd}}'),
    λ({
        'XF86AudioNext': 'cmd next',
        'XF86AudioPlay': 'cmd play',
        'XF86AudioPrev': 'cmd previous',
        'XF86AudioStop': 'cmd stop',
    }, fmt=f'{Exec} ~/bin/pl {{cmd}}'),
    λ({
        f'{M4}+{Sh}+a': 'attach',
        f'{M4}+{Sh}+s': 'move_window',
        f'{M4}+{Ct}+grave': 'i3_menu',
        f'{M1}+g': 'goto_win',
        f'{M4}+{Ct}+g': 'movews',
        f'{M1}+{Ct}+g': 'ws',
    }, fmt='$menu {cmd}'),
    λ({
        f'{M4}+{Ct}+q': 'kill',
        f'{M4}+5': '[floating] floating disable, unmark "^_all_$"',
        f'{M4}+{Sh}+g': 'mark --replace _all_, move scratchpad',
        f'{M4}+g': '[con_mark="^_all_$"] scratchpad show',
        f'{M4}+q': 'fullscreen toggle',
        f'{M4}+y': 'sticky toggle',
    }),
])


def mode_resize(): return Δ([
    λ({
        'bottom': ['j', 's'],
        'left': ['h', 'a'],
        'right': ['l', 'd'],
        'top': ['k', 'w'],
    }, fmt='$actions resize {cmd} 4'),
    λ({
        'bottom': [f'{Sh}+j', f'{Sh}+s'],
        'left': [f'{Sh}+h', f'{Sh}+a'],
        'right': [f'{Sh}+l', f'{Sh}+d'],
        'top': [f'{Sh}+k', f'{Sh}+w'],
    }, fmt='$actions resize {cmd} -4'),
    ], bind=f'{M4}+r', name='%{T4}%{T-}'
 )

def mode_spec(): return Δ([
    λ({
        'e': '[urgent=latest] focus',
        'l': 'exec ~/bin/x11lock',
        f'{Sh}+d': 'floating toggle',
    }, exit=True),
    λ({
        f'{Sh}+t': 'gtk_theme',
        f'{Sh}+i': 'icon_theme',
        'i': 'pulse_input',
        'o': 'pulse_output',
        'm': 'xprop_show',
    }, fmt='$menu {cmd}', exit=True),
    ], bind=f'{M1}+e', name='%{T4}%{T-}'
)

def mode_wm(): return Δ([
    λ({
        f'grave': 'default',
        f'minus': 'splith',
        f'backslash': 'splitv',
        f't': 'tabbed',
    }, fmt='layout {cmd}', exit=True),
    λ({f'Tab': 'toggle'}, fmt='layout {cmd}', exit=False),
    λ({
        'horizontal': [f'{Sh}+h', f'{Sh}+l'],
        'vertical': [f'{Sh}+j', f'{Sh}+k'],
    }, fmt='split', exit=True),
    λ({
        'w': 'up',
        'a': 'left',
        's': 'down',
        'd': 'right',
    }, fmt='move {cmd}'),
    λ({
        f'{Sh}+plus': 'grow',
        'x': 'maxhor',
        'm': 'maximize',
        'y': 'maxvert',
        'c': 'none',
        f'{Sh}+c': 'resize',
        'revert_maximize': [f'{Sh}+m', f'{Sh}+x', f'{Sh}+y'],
        'shrink': [f'{Sh}+minus'],
    }, fmt='$actions'),
    λ({
        'hdown': [f'{Sh}+w'],
        'hup': [f'{Sh}+a'],
        'vleft': [f'{Sh}+s'],
        'vright': [f'{Sh}+d'],
    }, fmt='$actions {cmd} x2'),
    ], bind=f'{M4}+minus', name='%{T4}%{T-}',
)

class conf_gen(Enum):
    plain = plain()
    exec = exec()
    exec_always = exec_always()
    rules = rules()
    workspaces = workspaces()
    mode_default = mode_default()
    mode_resize = mode_resize()
    mode_spec = mode_spec()
    mode_wm = mode_wm()
