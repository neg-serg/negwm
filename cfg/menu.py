from enum import Enum

class menu(Enum):
    gap = '38'
    host = '::'
    i3cmd = 'i3-msg'
    left_bracket = '⟬'
    matching = 'fuzzy'
    modules = ['i3menu', 'winact', 'pulse_menu', 'xprop', 'props', 'gnome', 'xrandr']
    port = 31888
    prompt = '❯>'
    right_bracket = '⟭'
    rules_xprop = ['WM_CLASS', 'WM_WINDOW_ROLE', 'WM_NAME', '_NET_WM_NAME']
    use_default_width = '3840'
    xprops_list = [
        'WM_CLASS',
        'WM_NAME',
        'WM_WINDOW_ROLE',
        'WM_TRANSIENT_FOR',
        '_NET_WM_WINDOW_TYPE',
        '_NET_WM_STATE',
        '_NET_WM_PID'
    ]
