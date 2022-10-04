from enum import Enum
Δ = dict

def discord():
    return Δ(
        classw = ['discord'],
        geom = '1898x1273+1936+825',
        keybind_toggle = ['Mod4+v'],
        prog = 'discord'
    )

def im():
    return Δ(
        classw = ['KotatogramDesktop', 'vkteams', 'Skype', 'Slack', 'TelegramDesktop', 'zoom'],
        geom = '1304x2109+2536+2',
        keybind_toggle = ['Mod4+e'],
        tel = Δ(
            classw = ['KotatogramDesktop'],
            keybind_spec_subtag = ['t'],
            prog = 'kotatogram-desktop'
        )
    )

def ncmpcpp():
    return Δ(
        geom = '2251x828+753+1205',
        classw = ['ncmpcpp'],
        keybind_toggle = ['Mod4+f'],
        spawn = 'ncmpcpp',
    )

def neomutt():
    return Δ(
        classw = ['mutterfox'],
        geom = '3670x2228+104+0',
        instance = ['mutterfox', 'neomutt'],
        keybind_toggle = ['Mod4+n'],
        spawn = 'neomutt',
    )

def teardrop():
    return Δ(
        geom = '3840x1300+0+0',
        instance = ['teardrop'],
        keybind_toggle = ['Mod4+d'],
        spawn = 'teardrop'
    )

def torrment():
    return Δ(
        geom = '3840x1300+0+0',
        instance = ['torrment'],
        keybind_toggle = ['Mod4+t'],
        spawn = 'torrment'
    )

def transients():
    return Δ(
        geom = '1812x797+693+1310',
        match_all = ['True'],
        keybind_spec_toggle = ['a'],
        role = ['GtkFileChooserDialog', 'Organizer', 'Manager']
    )


def webcam():
    return Δ(
        geom = '2463x1880+1368+268',
        instance = ['webcam'],
        keybind_spec_toggle = ['w'],
        prog = '~/bin/webcam'
    )


class scratchpad(Enum):
    discord = discord()
    im = im()
    ncmpcpp = ncmpcpp()
    neomutt = neomutt()
    teardrop = teardrop()
    torrment = torrment()
    transients = transients()
    webcam = webcam()
