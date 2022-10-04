from enum import Enum
Δ = dict

def term(): return Δ(
        term = 'kitty',
        classw = 'term',
        exec_tmux = [['zsh', 'zsh']],
        font = 'Iosevka',
        font_size = 19,
        padding = [2, 2],
        statusline = 1
    )

def ncmpcpp(): return Δ(
        term = 'kitty',
        classw = 'ncmpcpp',
        exec = 'ncmpcpp',
        font = 'Iosevka',
        font_normal = 'Medium',
        font_size = 17,
        opacity = 0.95,
        padding = [4, 4],
    )

def nwim(): return Δ(
        term = 'kitty',
        classw = 'nwim',
        exec = '/usr/bin/nvim --listen localhost:7777',
        font = 'Iosevka',
        font_normal = 'Medium',
        font_size = 17,
        instance_group = 'smaller_term',
        opacity = 0.95,
        padding = [4, 4],
    )


def teardrop(): return Δ(
        term = 'kitty',
        classw = 'teardrop',
        exec = '/usr/bin/btop',
        font = 'Iosevka',
        font_normal = 'Medium',
        font_size = 17,
        instance_group = 'smaller_term',
        padding = [8, 8],
    )


def torrment(): return Δ(
        term = 'kitty',
        classw = 'torrment',
        exec_tmux = [['stig', '/usr/bin/stig']],
        font = 'Iosevka',
        font_size = 18,
        instance_group = 'smaller_term',
        padding = [8, 8],
    )

def neomutt(): return Δ(
        term = 'kitty',
        classw = 'neomutt',
        exec_dtach = 'neomutt',
        font = 'Iosevka',
        font_size = 17,
    )


class executor(Enum):
    ncmpcpp = ncmpcpp()
    neomutt = neomutt()
    nwim = nwim()
    teardrop = teardrop()
    term = term()
    torrment = torrment()
