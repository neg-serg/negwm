![banner](https://i.imgur.com/fgmuilL.png)

* [Screenshots](#screenshots)
* [What is it?](#what-is-it)
* [Why](#why)
* [Help](#help)
* [Installation](#installation)
* [General](#general)
* [Modules](#modules)
    * [Scratchpad](#scratchpad)
    * [Circle](#circle)
    * [Remember focused](#remember-focused)
    * [Menu](#menu)
    * [Actions](#actions)
    * [Executor](#executor)
    * [fs](#fs)

# Screenshots

![terminal_shot](https://i.imgur.com/O08SzU3.png)
![nvim_shot](https://i.imgur.com/Tqfu65R.png)
![unixporn_like_shot](https://i.imgur.com/z1arTLh.png)

# What is it?

For now this collection of modules for i3 includes

_negwm_ : application that run all modules and handle configuration of i3 and modules on python. Also handles config updating.

# Why

It is only my attempt to port the best UX parts from ion3/notion and also improve it when possible. But if you try I may find that things,
like better scratchpad or navigation very useful.

# Help

```man
i3 negwm daemon script.

This module loads all negwm an start it via main's manager mailoop. Inotify-based watchers for all negwm S-expression-based configuration
spawned here, to use it just start it from any place without parameters. Moreover it contains pid-lock which prevents running several times.

Usage:
    ./negwm.py
```

# Installation

Negwm suggests that your main i3 config directory is `$XDG_CONFIG_HOME/i3`, so you need to set up your `$XDG_CONFIG_HOME` variable before
install, via `/etc/profile`, some kind of `.zshenv` or smth else depending or your environment, it is mandatory to install.

Before install make sure to backup your i3 configuration, install script should do it automatically, but it's better to do it by hand for
the reliability reasons.

The most simple way to install it for now is to use install from repo:

`curl https://raw.githubusercontent.com/neg-serg/negwm/master/bin/install | sh`

Also you can clone this to any dir and run `<negwm_dir>/bin/install`

After install check it via smth like:

```
cd $XDG_CONFIG_HOME/negwm
./bin/run
```

If everything is ok then you can use new i3 config example, where `Mod4- Shift + '`
is i3wm reloading, after reload you should get i3 with `negwm` plugins on the board.

# General

Some general notes:

`negwm` works as a server in port 15555. It splited by various modules.
You can call any function of any module with something like this:

```
echo 'scratchpad toggle ncmpcpp'|nc localhost 15555 -v -w 0
```

Where 1st argument is module, 2nd is function and another is parameters.

Most of modules supports dynamic reloading of configs as you save the file, so there is no need to manually reload them. Anyway you can
reload negwm manually, for example to reload `executor`:

```
echo 'executor reload'|nc localhost 15555 -v -w 0
```

At first you need to add something in run and add it to config:

Start it via systemd user service:

```cfg
exec_always systemctl --user restart --no-block negwm.service
```

To restart negwm after i3 reload, `negwm.py` should close file automatically, after i3 reload/restart so you can simply run it after
restart.

# Modules

## Scratchpad

Named ion3-like scratchpads with a whistles and fakes.

Named scratchpad is something like tabs for windows. You can create scratchpad with several rules like `im`, `player`, etc and attach
windows to it. Then it make some magic to support some kind of "next tab" for this group, etc.

Look at `cfg/scratchpad.py` for the more info.

Possible matching rules are:
"class", "instance", "role", "class_r", "instance_r", "name_r", "role_r", 'match_all'

It supports both strings and regexes and also need geom to create virtual placeholder for this windows, where all matched windows are
attached to.

Some interesting commands:

```cfg
    dialog: toggle dialogs
    hide_current: hide current scratchpad despite of type
    hide: hide scratchpad
    next: go to the next window in scratchpad
    show: show scratchpad
    subtag: you can create groups inside groups.
    toggle: show/hide this named scratchpad, very useful
```

Interesting parts here:

Use `toggle` to toggle this specific scratchpad on / off. It saves current selected window after hiding.

Use `next` to go to the next of opened named scratchpad window for the current scratchpad. for example with im case you will iterate over
`telegram` and `skype` windows if they are opened

Use `hide_current` to hide any scratchpad with one hotkey.

Use `subtag` if you want to iterate over subset of named scratchpad or run command for a subset of scratchpad. For example use `subtag im
tel` if you want to run telegram or go to the window of telegram if it's opened despite of another im windows like skype opened or not.

Use `dialog` to show dialog window. I have placed it in the separated scratchpad for convenience.

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
    modules = ['i3menu', 'winact', 'pulse_menu', 'xprop', 'props', 'xrandr']
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
