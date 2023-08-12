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
    ./main.py
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
python3

>>> import negwm.main
>>> negwm.main.run()
```

Если запуск прошел успешно, то будет сгенерен конфиг для i3, а negwm можно порелоадить с помощью `Mod4- Shift + '`,
после реалоада все модули должны работать.

# После установки

## Опциональные зависимости

```
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
```

Если у вас arch linux быстро поставить это можно так:

```
pacman -Syu alacritty dunst kitty libxrandr picom pulseaudio rofi tmux xdo zsh --noconfirm
```

## Хранимая конфигурация

Конфигурация хранится в директории `$XDG_CONFIG_HOME/negwm`. Каждый файл с расширенрием `.cfg` соответствует своему модулю.
Примеры конфига есть в `example`.

## Генератор конфига

Генератор конфига был сделан для того, чтобы изменения в конфиге, которые относятся к модулям, можно было писать в них самих. Также есть
генерилка для конфига самого i3.

Как его следует читать: в `configurator.cfg` есть набор полей, с синтаксисом как в python enum(https://docs.python.org/3/library/enum.html).
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
`$XDG_CACHE_HOME/negwm/cfg`, так что обычно нет необходимости перегружать их руками. Тем не менее это можно сделать с помощью команды `reload`.
Пример для модуля `circle`:

```
echo 'circle reload'|nc localhost 15555 -v -w 0
```

# Описание модулей

Как известно в X11 у окон есть разные атрибуты, такие как `WM_CLASS`, `WM_NAME` и др. В конфигах используется "class", "instance", "role"
для обычных строковых атрибутов, "class_r", "instance_r", "name_r", "role_r" для regex'ов.

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

Улучшенная версия run-or-raise(см. например https://vickychijwani.me/blazing-fast-application-switching-in-linux/), с прыжками по кругу, поддержкой подгрупп, приоритетов и др.

Идея работы этой штуки такая:

Если нет окна, которое соответствует правилам из списка, тогда запускается `prog`, в противном случае приложение запускается.

Также подгруппами подходящих под правила окон можно итерироваться. Так что об этом можно думать как о чем-то вроде рабочего стола, только не
в смысле визуального расположения, а в смысле группировки окон по некому признаку. Это переключение работает всегда вне зависимости
от текущего рабочего стола или монитора. 

Пример конфига:
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

В этом примере если нажать `mod4+w` тогда `firefox` стартует, если он не был запущен ранее, в противном случае выполняется прыжок к нему согласно приоритету.
Для этого примера представим, что `tor-browser` уже был запущен, тогда можно будет прыгать между всеми перечисленными браузерами через `mod4+w`, а с помощью
`mod1+e -> 5` можно будет перейти на `tor-browser`.

Некоторые полезные функции:

```cfg
    next: go to the next window
    subtag: go to the next subtag window
```

## Lastgo

Штука которая запоминает предыдущее окно и позволяет прыгнуть на него вне зависимости от того какой рабочий стол используется.
Это нужно потому что в i3 alt-tab по-умолчанию не запоминает какое окно было предыдущим, а тут есть прямое сохранение истории.

Пример конфига:

```cfg
class lastgo(Enum):
    autoback = ['pic', 'gfx', 'vm']
```

autoback это список рабочих столов, которой означает, что если на этом столе нет ни одного окна, то выполняется прыжок на предыдущее окно.

Некоторые полезные функции:

```cfg
    switch: go to previous window
    focus_next: focus next window
    focus_prev: focus previous window
    focus_next_visible: focus next visible window
    focus_prev_visible: focus previous visible window
```

## Actions

Разные приколы чтобы эмулировать UX(поведение) из 2bwm(https://github.com/venam/2bwm). Оно активно не используется, что там есть можно
посмотреть в исходниках `negwm/modules/actions.py` Желания поддерживать это и документировать большого нет, но оно работает.

## Fullscreen

Специальный модуль, который нужен для хакинга панели polybar для некоторых перечисленных рабочих столов.

## Support

If you like my stuff, you can [buy me a coffee](https://www.buymeacoffee.com/negserg).
