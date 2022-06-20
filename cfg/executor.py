from enum import Enum
Δ = dict


class executor(Enum):
    ncmpcpp = Δ(
        term = 'kitty',
        classw = 'ncmpcpp',
        exec = 'ncmpcpp',
        font = 'Iosevka',
        font_normal = 'Medium',
        font_size = 17,
        opacity = 0.8,
        padding = [12, 12],
    )

    neomutt = Δ(
        classw = 'neomutt',
        exec_dtach = 'neomutt',
        font = 'Iosevka',
        font_size = 17,
    )

    nwim = Δ(
        classw = 'nwim',
        exec = '/usr/bin/nvim --listen localhost:7777',
        font = 'Iosevka',
        font_normal = 'Medium',
        font_size = 17,
        opacity = 0.95,
        padding = [4, 4],
    )

    teardrop = Δ(
        classw = 'teardrop',
        exec = '/usr/bin/btop',
        font = 'Iosevka',
        font_normal = 'Iosevka',
        font_size = 14,
        padding = [8, 8],
        statusline = 0
    )

    torrment = Δ(
        classw = 'torrment',
        exec_tmux = [['stig', '/usr/bin/stig']],
        font = 'Iosevka',
        font_size = 18,
        padding = [8, 8],
        statusline = 0
    )

    term = Δ(
        classw = 'term',
        exec_tmux = [['zsh', 'zsh']],
        font = 'Iosevka',
        font_size = 19,
        padding = [2, 2],
        statusline = 1
    )
