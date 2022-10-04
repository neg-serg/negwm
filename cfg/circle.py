from enum import Enum
Δ = dict

def bitwig(): return Δ(
    classw = ['Bitwig Studio'],
    keybind_next = ['Mod4+Control+b'],
    prog = 'bitwig-studio',
    ws = 'sound'
)

def doc(): return Δ(
    classw = ['Zathura', 'cr3'],
    keybind_next = ['Mod4+o'],
    ws = 'doc'
)

def nwim(): return Δ(
    classw = ['nwim'],
    keybind_next = ['Mod4+1'],
    spawn = 'nwim',
    ws = 'dev'
)

def obs(): return Δ(
    classw = ['obs'],
    keybind_toggle = ['Mod4+Shift+o'],
    prog = 'obs',
    ws = 'obs'
)

def remote(): return Δ(
    classw = ['xfreerdp', 'reminna', 'org.remmina.Remmina'],
    keybind_toggle = ['Mod4+Control+5'],
    ws = 'remote'
)

def steam(): return Δ(
    classw = ['Steam', 'steam'],
    keybind_next = ['Mod4+Shift+e'],
    prog = 'zsh -c "flatpak run com.valvesoftware.Steam"',
    ws = 'steam'
)

def nsxiv(): return Δ(
    classw = ['Nsxiv'],
    keybind_next = ['Mod4+Control+c'],
    prog = "~/bin/sx ~/dw/ ~/tmp/shots/",
    wallpaper = {'classw': ['Nsxiv'], 'keybind_subtag': ['Mod4+Shift+c'], 'prog': '~/bin/wl --show'},
    ws = 'gfx'
)

def term(): return Δ(
    instance = ['term'],
    keybind_next = ['Mod4+x'],
    spawn = 'term',
    ws = 'term'
)

def vid(): return Δ(
    classw = ['mpv'],
    keybind_next = ['Mod4+b'],
    mpd_shut = 0,
    prog = '~/bin/pl rofi 1st_level ~/vid/new',
    ws = 'gfx'
)

def vm(): return Δ(
    classw = ['spicy'],
    class_r = ['^[Qq]emu-.*$'],
    keybind_next = ['Mod4+Control+v'],
    ws = 'vm'
)

def web(): return Δ(
    classw = ['firefox', 'firefoxdeveloperedition', 'Tor Browser', 'Chromium'],
    keybind_next = ['Mod4+w'],
    prog = 'firefox',
    firefox = Δ(
        classw = ['firefox'],
        keybind_spec_subtag = ['f'],
        prog = 'firefox'
    ),
    tor = Δ(
        classw = ['Tor Browser'],
        keybind_spec_subtag = ['5'],
        prog = 'tor-browser rutracker.org'
    ),
    ws = 'web'
)


class circle(Enum):
    bitwig = bitwig()
    doc = doc()
    nsxiv = nsxiv()
    nwim = nwim()
    obs = obs()
    remote = remote()
    steam = steam()
    term = term()
    vid = vid()
    vm = vm()
    web = web()
