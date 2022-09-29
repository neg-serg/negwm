![banner](https://i.imgur.com/fgmuilL.png)

# Скриншоты

![terminal_shot](https://i.imgur.com/O08SzU3.png)
![nvim_shot](https://i.imgur.com/Tqfu65R.png)
![unixporn_like_shot](https://i.imgur.com/z1arTLh.png)

# Что это

Это порт лучших фич UX из ion3/notion, а также некоторые его улучшения с максимальным акцентом на circle и bscratch.

```man
i3 negwm daemon script.

This module loads all negwm an start it via main's manager mailoop. Inotify-based watchers for all negwm S-expression-based configuration
spawned here, to use it just start it from any place without parameters. Moreover it contains pid-lock which prevents running several times.

Usage:
    ./negwm.py
```

# Установка

## Переменные окружения

- Для корректной работы перед установкой необходимо установить переменную окружения `XDG_CONFIG_HOME`, например через `.zshenv` или `/etc/profile`

## Автоматическая установка при помощи скрипта

`curl https://raw.githubusercontent.com/neg-serg/negwm/master/bin/install | sh`

## Альтернативная установка

Осуществляется путем запуска сценария `<negwm_dir>/bin/install`

## Проверка после установки

```
cd $XDG_CONFIG_HOME/negwm
./bin/run
```

Если запуск прошел успешно, то будет сгенерен конфиг для i3, а negwm можно порелоадить с помощью `Mod4- Shift + '`,
после реалоада все модули должны работать.

# После установки

## Опциональные зависимости

'alacritty: terminal emulator'
'dunst: x11 notification daemon'
'kitty: terminal emulator'
'libxrandr: xrandr support'
'picom: X11 compositing support'
'pulseaudio: general-purpose sound server'
'rofi: x11 menu'
'tmux: terminal multiplexor'
'xdo: x11 window manipulation tools'
'zsh: better shell'

## Хранимая конфигурация

Конфигурация хранится в директории `$XDG_CONFIG_HOME/negwm/cfg`. Каждый файл с расширенрием `.py` соответствует своему модулю.

## Генератор конфига

Генератор конфига был сделан для того, чтобы изменения в конфиге, которые относятся к модулям, можно было писать в них самих. Также есть
генерилка для конфига самого i3.

Как его следует читать: в `cfg/conf_gen.py` есть набор полей, с синтаксисом как в python enum(https://docs.python.org/3/library/enum.html).
Каждому полю может соответствовать функция, которая на основе шаблона генерит конфиг.

## Модули

Есть два варианта вызова функций в модулях. Используется обычный async event loop, который вычитывает строки по одной, сплитит их с помощью
.split() и потом отсылает "сообщение" туда куда следует.

Любые функции модулей можно вызывать либо `send_msg` внутри самого `negwm`, либо отправлять сообщения на порт `15555` в таком формате,     :
например как `<имя модуля>` `<команда>` `<параметры через пробел>`, например                                                                     :

```
circle next term.
```

С точки зрения вызова это может выглядеть например так:

`echo 'circle next term' | /usr/bin/nc localhost 15555 -w 0`

# Главное

`negwm` это сервис, который поднят на порту 15555, в который можно писать команды с предложенным выше форматом, например:

```
echo 'scratchpad toggle ncmpcpp'|nc localhost 15555 -v -w 0
```

Большинство модулей поддерживают автоматический reload конфигов, как только файл с ними сохраняется. Создается кэш с расширением `.pickle` в
`<negwm_dir>/cache/cfg`, так что обычно нет необходимости перегружать их руками. Тем не менее это можно сделать с помощью команды `reload`.
Пример для модуля `executor`:

```
echo 'executor reload'|nc localhost 15555 -v -w 0
```

Negwm можно запускать например с помощью systemd:

```cfg
exec_always systemctl --user restart --no-block negwm.service
```

Предлагаемый конфиг устроен таким образом, что можно можно сделать `i3-msg reload` и `negwm` будет перезагружен автоматически.

# Описание модулей

Как известно в X11 у окон есть разные атрибуты, такие как `WM_CLASS`, `WM_NAME` и др. В конфигах используется "class", "instance", "role"
для обычных строковых атрибутов, "class_r", "instance_r", "name_r", "role_r" для regex'ов и match_all псевдоатрибут, который просто матчит всё подряд.

## Scratchpad

Именованные скратчпады как в ion3, со свистелками и перделками.

Именованные скратчпады это по смыслу как что-то типа вкладок для окон. Можно создавать скратчпад, которые представляют собой плавающие группы
окон, например `im`, `player`, etc и правила для них, чтобы окна на них привязывались. Тогда появляется всякая магия, которая позволяет делать
что-то типа "next tab" для этой группы окон и др.

Модуль находится в `modules/scratchpad.py`, можно посмотреть как устроен.

Некоторые интересные команды для скратчпадов:

```cfg
    dialog: toggle dialogs
    hide_current: hide current scratchpad despite of type
    hide: hide scratchpad
    next: go to the next window in scratchpad
    show: show scratchpad
    subtag: you can create groups inside groups.
    toggle: show/hide this named scratchpad, very useful
```

Наиболее интересные функции тут это:

`toggle` используется чтобы включить/выключить скратчпад. Также оно умеет сохранять текущее выбранное окно.

`next` используется чтобы перейти к следующему окну в группе. Например для группы im которая приведена как пример это приведет к прыжкам между telegram и skype если они запущены.

`hide_current` используется чтобы спрятать любой скратчпад. Это нужно чтобы не думать какой из них конкретно открыт, а можно было всё это делать одной и той же кнопкой.

`subtag` используется когда одну группу нужно разбить на подмножество и итерироваться по подмножеству для данного именованного скратчпада или запускать что-то из этой подгруппы.
Например для im можно добавить подгруппу tel, которая будет итерироваться по всем telegram или запускать их, при этом другие окна в основной группе будут игнорироваться.

`dialog` чтобы показать диалоговое окно из разных приложений, оно кладется в скратчпад для удобства.

## Circle

Better run-or-raise, with jump in a circle, subtags, priorities and more. Run-or-raise is the following:

If there is no window with such rules then start `prog` Otherwise go to the window.

More of simple going to window you can **iterate** over them. So it's something like workspaces, where workspace is not about view, but
about semantics. This works despite of current monitor / workspace and you can iterate over them with ease.

Possible matching rules are:
"class", "instance", "role", "class_r", "instance_r", "name_r", "role_r", 'match_all'

circle config example:
```python3

Δ = dict
class circle(Enum):
    web = Δ(
        classw = ['firefox', 'firefoxdeveloperedition', 'Tor Browser', 'Chromium'],
        keybind_default_next = ['Mod4+w'],
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
```

For this example if you press `mod4+w` then `firefox` starts if it's not started, otherwise you jump to it, because of priority. Let's
consider then that `tor-browser` is opened, then you can iterate over two of them with `mod4+w`. Also you can use subtags, for example
`mod1+e -> 5` to run / goto window of tor-browser.

Some useful commands:

```cfg
    next: go to the next window
    subtag: go to the next subtag window
```

## Remember focused

Goto to the previous window, not the workspace. Default i3 alt-tab cannot to remember from what window alt-tab have been done, this mod fix
at by storing history of last selected windows.

config_example:

```cfg
class RememberFocused(Enum):
    autoback = ['pic', 'gfx', 'vm']
```

remember_focused commands:

```cfg
    switch: go to previous window
    focus_next: focus next window
    focus_prev: focus previous window
    focus_next_visible: focus next visible window
    focus_prev_visible: focus previous visible window
```

## Menu

Menu module including i3-menu with hackish autocompletion, menu to attach window to window group(circled) or target named scratchpad(nsd)
and more.

It consists of main `menu.py` with the bindings to the menu modules, for example:

```cfg
    attach
    autoprop 
    goto_win 
    gtk_theme
    i3_menu 
    icon_theme
    movews 
    pulse_input 
    pulse_mute 
    pulse_output 
    show_props 
    ws 
    xprop_show
    xrandr_resolution
```

It loads appropriate modules dynamically, to handle it please edit `cfg/menu.py` Too many of options to document it properly.

menu cfg example:

```python3
class menu(Enum):
    gap = '38'
    host = '::'
    i3cmd = 'i3-msg'
    matching = 'fuzzy'
    modules = ['i3menu', 'winact', 'pulse_menu', 'xprop', 'props', 'gnome', 'xrandr']
    port = 31888
    use_default_width = '3840'
    rules_xprop = ['WM_CLASS', 'WM_WINDOW_ROLE', 'WM_NAME', '_NET_WM_NAME']
    xprops_list = ['WM_CLASS', 'WM_NAME', 'WM_WINDOW_ROLE', 'WM_TRANSIENT_FOR', '_NET_WM_WINDOW_TYPE', '_NET_WM_STATE', '_NET_WM_PID']

    prompt = '❯>'
    left_bracket = '⟬'
    right_bracket = '⟭'
```

Also it contains some settings for menus.

## Actions

Various stuff to emulate some 2bwm UX. I do not use it actively for now, so too lazy to write good documentation for it but if you are
interested you are free to look at `lib/actions.py` source code.

## Executor

Module to create various terminal windows with custom config and/or tmux session handling. Supports a lot of terminal emulators, but for now
only `alacritty` has nice support, because of I think it's the best terminal emulator for X11 for now.

i3 config example: _nothing_

For now I have no any executor bindings in the i3 config, instead I use it as helper for another modules. For example you can use spawn
argument for `circle` or `scratchpad`. Let's look at `cfg/circle.py` It contains:

```python3
Δ = dict

class executor(Enum):
    term = Δ(
        classw = 'term',
        exec_tmux = [['zsh', 'zsh']],
        font = 'Iosevka',
        font_size = 19,
        padding = [8, 8],
        statusline = 1
    )
```

Where spawn is special way to create terminal window with help of executor.

So it create tmuxed window with alacritty(default) config with Iosevka:18 font. Another examples:

```python3
nwim = Δ(
    classw = 'nwim',
    exec = '/usr/bin/nvim --listen localhost:7777',
    font = 'Iosevka',
    font_normal = 'Medium',
    font_size = 17,
    opacity = 0.95,
    padding = [8, 8],
)
```

Creates neovim window without tmux, without padding, with Iosevka 17 sized font and alacritty-specific feature of using Iosevka Medium for
the regular font.

Look at the `lib/executor.py` to learn more.

## fs

Fullscreen panel hacking.
