![banner](https://i.imgur.com/fgmuilL.png)

# Screenshots

![terminal_shot](https://i.imgur.com/O08SzU3.png)
![nvim_shot](https://i.imgur.com/Tqfu65R.png)
![unixporn_like_shot](https://i.imgur.com/z1arTLh.png)

- [Screenshots](#screenshots)
- [What is it?](#what-is-it-)
- [main](#main)
- [modules](#modules)
  - [scratchpad](#scratchpad)
  - [circle](#circle)
  - [remember_focused](#win-history)
  - [menu](#menu)
  - [vol](#vol)
  - [actions](#win-action)
  - [executor](#executor)
  - [fs](#fs)
  - [procs to run by negi3wm as another process](#procs-to-run-by-negi3wm-as-another-process)
- [Installation](#installation)
- [Dependencies:](#dependencies-)
  - [Modern python3 with modules:](#modern-python3-with-modules-)
- [Run](#run)
- [Performance](#performance)
  - [Performance profiling](#performance-profiling)
- [Why](#why)
- [Bugs](#bugs)
- [Video Demonstration](#video-demonstration)

# What is it?

For now this collection of modules for i3 includes

# main

_negi3wm_ : application that run all modules and handle configuration of
i3 and modules on python. Also handles TOML-configs updating.

Some general notes:

`negi3wm.py` works as a server and `send` is a client. To look at the last
actual list of command for modules you can look at `self.bindings` of some
module. Most of them supports dynamic reloading of TOML-based configs as you
save the file, so there is no need to manually reload them. Anyway you can
reload negi3wm manually:

At first you need to add something in negi3wm_run and add it to config:

```cfg
exec_always ~/.config/negi3wm/negi3wm_run &
```

Current negi3wm_run is:

```bash
${XDG_CONFIG_HOME}/negi3wm/negi3wm.py --start >> ${HOME}/tmp/negi3wm.log 2>&1 &
make -C ${XDG_CONFIG_HOME}/negi3wm/ &
```

Interesting parts here are:

```bash
${XDG_CONFIG_HOME}/negi3wm/negi3wm.py --start >> ${HOME}/tmp/negi3wm.log 2>&1 &
```

To restart negi3wm after i3 reload, `negi3wm.py` should close file
descriptor automatically, after i3 reload/restart so you can simply run it
after restart.

```bash
make -C ${XDG_CONFIG_HOME}/negi3wm/ &
```

To recompile `send` client.

# modules

## scratchpad

Named ion3-like scratchpads with a whistles and fakes.

Named scratchpad is something like tabs for windows. You can create scratchpad
with several rules like `im`, `player`, etc and attach windows to it. Then it
make some magic to support some kind of "next tab" for this group, etc.

Config example(`cfg/scratchpad.cfg`):

```toml
[im]
class = [ "ViberPC", "VK", "zoom", "IGdm"]
class_r = [ "[Tt]elegram.*", "[Ss]kype.*",]
geom = "548x1165+1368+3"
```

Look at `cfg/scratchpad.cfg` for the more info.

Possible matching rules are:
"class", "instance", "role", "class_r", "instance_r", "name_r", "role_r", 'match_all'

It supports both strings and regexes and also need geom to create virtual
placeholder for this windows, where all matched windows are attached to.

Some interesting commands:

```cfg
show: show scratchpad
hide: hide scratchpad
next: go to the next window in scratchpad
toggle: show/hide this named scratchpad, very useful
hide_current: hide current scratchpad despite of type
subtag: you can create groups inside groups.
dialog: toggle dialogs
```

i3 config example:

```cfg
set $scratchpad exec --no-startup-id ${XDG_CONFIG_HOME}/negi3wm/send scratchpad

bindsym Mod1+e mode "SPEC"

bindsym Mod4+f $scratchpad toggle ncmpcpp
bindsym Mod4+e $scratchpad toggle im
bindsym Mod4+d $scratchpad toggle teardrop
bindsym Mod4+v $scratchpad toggle discord
bindsym Mod4+3 $scratchpad next
bindsym Mod4+s $scratchpad hide_current

bindsym Mod4+Control+Shift+R $scratchpad geom_restore
bindsym Mod4+Control+Shift+D $scratchpad geom_dump
bindsym Mod4+Control+Shift+S $scratchpad geom_autosave

mode "SPEC" {
    bindsym Mod4+s $scratchpad subtag im skype, mode "default"
    bindsym Mod1+s $scratchpad subtag im skype, mode "default"
    bindsym s $scratchpad subtag im skype, mode "default"
    bindsym Mod4+t $scratchpad subtag im tel, mode "default"
    bindsym Mod1+t $scratchpad subtag im tel, mode "default"
    bindsym t $scratchpad subtag im tel, mode "default"
    bindsym m $scratchpad toggle mutt, mode "default"
    bindsym w $scratchpad toggle webcam, mode "default"
    bindsym a mode "default", $scratchpad dialog
}
```

Interesting parts here:

Use `toggle` to toggle this specific scratchpad on / off. It saves current
selected window after hiding.

Use `next` to go to the next of opened named scratchpad window for the current
scratchpad. for example with im case you will iterate over `telegram` and
`skype` windows if they are opened

Use `hide_current` to hide any scratchpad with one hotkey.

Use `subtag` if you want to iterate over subset of named scratchpad or run
command for a subset of scratchpad. For example use `subtag im tel` if you want
to run telegram or go to the window of telegram if it's opened despite of
another im windows like skype opened or not.

Use `dialog` to show dialog window. I have placed it in the separated
scratchpad for convenience.

## circle

Better run-or-raise, with jump in a circle, subtags, priorities and more.
Run-or-raise is the following:

If there is no window with such rules then start `prog` Otherwise go to the
window.

More of simple going to window you can **iterate** over them. So it's something
like workspaces, where workspace is not about view, but about semantics. This
works despite of current monitor / workspace and you can iterate over them with
ease.

Config example (`cfg/circle.cfg`):

```toml
[web]
class = [ "firefox", "Waterfox", "Tor Browser", "Chromium"]
priority = "firefox"
prog = "firefox"

[web.firefox]
class = [ "Firefox", "Nightly", "Navigator"]
prog = "firefox"
```

Where `web` is a tag and `web firefox` is subtag.

Possible matching rules are:
"class", "instance", "role", "class_r", "instance_r", "name_r", "role_r", 'match_all'

i3 config example:

```cfg
set $circle exec --no-startup-id $XDG_CONFIG_HOME/negi3wm/send circle

bindsym Mod4+Control+c $circle next sxiv
bindsym Mod4+Shift+c $circle subtag sxiv wallpaper
bindsym Mod4+x $circle next term
bindsym Mod4+1 $circle next nwim

bindsym Mod1+e mode "SPEC"

mode "SPEC" {
bindsym 5 mode "default", Controlircle subtag web tor
bindsym y mode "default", Controlircle subtag web yandex
bindsym f mode "default", Controlircle subtag web firefox
}
```

For this example if you press `mod4+w` then `firefox` starts if it's not
started, otherwise you jump to it, because of priority. Let's consider then
that `tor-browser` is opened, then you can iterate over two of them with
`mod4+w`. Also you can use subtags, for example `mod1+e -> 5` to run / goto
window of tor-browser.

Some useful commands:

```cfg
next: go to the next window
subtag: go to the next subtag window
```

## remember_focused

Goto to the previous window, not the workspace. Default i3 alt-tab cannot to
remember from what window alt-tab have been done, this mod fix at by storing
history of last selected windows.

i3 config example:

```cfg
set $remember_focused exec --no-startup-id $XDG_CONFIG_HOME/negi3wm/send remember_focused
bindsym Mod4+grave $remember_focused focus_next_visible
bindsym Mod4+Shift+grave $remember_focused focus_prev_visible
bindsym Mod1+Tab $remember_focused switch
bindsym Mod4+slash $remember_focused switch
```

remember_focused commands:

```cfg
switch: go to previous window
focus_next: focus next window
focus_prev: focus previous window
focus_next_visible: focus next visible window
focus_prev_visible: focus previous visible window
```

## menu

Menu module including i3-menu with hackish autocompletion, menu to
attach window to window group(circled) or target named scratchpad(nsd) and
more.

It consists of main `menu.py` with the bindings to the menu modules, for example:

```python
self.bindings = {
    "cmd_menu": self.i3menu.cmd_menu,

    "xprop": self.xprop.xprop,

    "autoprop": self.props.autoprop,
    "show_props": self.props.show_props,

    "pulse_output": self.pulse_menu.pulseaudio_output,
    "pulse_input": self.pulse_menu.pulseaudio_input,

    "ws": self.winact.goto_ws,
    "goto_win": self.winact.goto_win,
    "attach": self.winact.attach_win,
    "movews": self.winact.move_to_ws,

    "gtk_theme": self.gnome.change_gtk_theme,
    "icon_theme": self.gnome.change_icon_theme,

    "xrandr_resolution": self.xrandr.change_resolution_xrandr,

    "reload": self.reload_config,
}
```

It loads appropriate modules dynamically, to handle it please edit `cfg/menu.cfg`.
Too many of options to document it properly.

menu cfg example:

```toml
modules = ['i3menu', 'winact', 'pulse_menu', 'xprop', 'props', 'gnome', 'xrandr',]
```

Also it contains some settings for menus.

i3 config example:

```cfg
set $menu exec --no-startup-id ${XDG_CONFIG_HOME}/negi3wm/send menu
bindsym Mod1+g $menu goto_win
bindsym Mod4+g $menu ws
bindsym Mod4+Control+g $menu movews
bindsym Mod4+Control+grave $menu cmd_menu
```

## vol

Contextual volume manager. Handles mpd by default. If mpd is stopped then
handles mpv with mpvc if the current window is mpv, or with sending 0, 9 keys
to the mpv window if not. To use it add to i3 config something like this:

```cfg
set $volume exec --no-startup-id ${XDG_CONFIG_HOME}/negi3wm/send vol
bindsym XF86AudioLowerVolume $volume d
bindsym XF86AudioRaiseVolume $volume u
```

Command list:

```cfg
u: volume up
d: volume down
reload: reload module.
```

## actions

Various stuff to emulate some 2bwm UX. I do not use it actively for now, so too
lazy to write good documentation for it but if you are interested you are free
to look at `lib/actions.py` source code.

## executor

Module to create various terminal windows with custom config and/or tmux
session handling. Supports a lot of terminal emulators, but for now only
`alacritty` has nice support, because of I think it's the best terminal
emulator for X11 for now.

i3 config example: _nothing_

For now I have no any executor bindings in the i3 config, instead I use it as
helper for another modules. For example you can use spawn argument for `circle`
or `scratchpad`. Let's look at `cfg/circle.cfg`. It contains:

```toml
[term]
class = [ "term",]
instance = [ "term",]
spawn = "term"
```

Where spawn is special way to create terminal window with help of executor.
Then look at `cfg/executor.cfg`. It contains:

```toml
[term]
class="term"
font="Iosevka"
font_size=18
```

So it create tmuxed(default behaviour) window with alacritty(default) config
with Iosevka:18 font. Another examples:

```toml
[teardrop]
class="teardrop"
font="Iosevka"
font_size=18
postfix='-n mixer ncpamixer \; neww -n atop atop \; neww -n stig stig \; neww -n tasksh tasksh \; select-window -t 2'
```

Creates tmuxed window with several panes with ncpamixer, atop, stig and tasksh.

```toml
[nwim]
class="nwim"
font="Iosevka"
font_size=15.5
font_style_normal="Medium"
with_tmux=0
x_padding=0
y_padding=0
prog='NVIM_LISTEN_ADDRESS=/tmp/nvimsocket nvim'
```

Creates neovim window without tmux, without padding, with Iosevka 15.5 sized
font and alacritty-specific feature of using Iosevka Medium for the regular
font.

Look at the `lib/executor.py` to learn more.

Please look for config examples at [my
dotfiles](https://github.com/neg-serg/dotfiles/blob/master/term-colorschemes/.config/colorschemes/neg-dark3.sh).

## fs

Fullscreen panel hacking.

## procs to run by negi3wm as another process

~~There are processes, not threads, separated from the main negi3wm event
loop to reach better performance or another goals.~~

For now there are no any processes started by negi3wm. I've considered that
this scheme of loading can cause various race condictions and another stability
issues.

Current procs binaries intended to be run from polybar.

To use ws please add to polybar config something like this:

```config
[module/ws]
type = custom/script
exec = PYTHONPATH=${XDG_CONFIG_HOME}/negi3wm python -u -m bin.polybar_ws 2> /dev/null
exec-if = sleep 1
format-background = ${color.mgf}
format = <label>
format-suffix = " "
tail = true
```

I created ws module because of some race condition in polybar when ws switching
is too fast, but for now it also provides good integration with i3, for example
you can see current binding mode in the left of workspace widget with custom
font and also create custom markup for any of workspace as you like.

To use fast mpd volume notification module use this:

```config
[module/volume]
type = custom/script
interval = 0
format-background = ${color.mgf}
exec = PYTHONPATH=${XDG_CONFIG_HOME}/negi3wm python -u -m proc.polybar_vol 2> /dev/null
exec-if = sleep 1
tail = true
```

I created because of I have nice wheel on the keyboard, so it's nice to see
very fast volume updating for me. For now I have DAC with extreme-quality
in-chip physical digital volume regulator, so it's no longer unnecessary but
I still want to see `Vol: 0` / `Vol: 100` anyway :)

_polybar_ws_: async current i3 workspace printer for polybar.

_polybar_vol_ : async MPD printer for polybar.

# Installation

Negi3wm suggests that your main i3 config directory is `$XDG_CONFIG_HOME/negi3wm`,
so you need to set up your `$XDG_CONFIG_HOME` variable before install, via
`/etc/profile`, some kind of `.zshenv` or smth else depending or your
environment, it is mandatory to install.

Before install make sure to backup your i3 configuration, install script should
do it automatically, but it's better to do it by hand for the reliability
reasons.

The most simple way to install it for now is to use install.sh from repo:

```
curl https://raw.githubusercontent.com/neg-serg/negi3wm/master/bin/install.sh | sh
```

After install check it via smth like:

```
cd $XDG_CONFIG_HOME/negi3wm
./negi3wm.py
```

If everything is ok then you can use new i3 config example, where `Mod4

- Shift + '`is i3wm reloading, after reload you should get i3 with`negi3wm`
  plugins on the board.

# Dependencies:

## Modern python3 with modules:

- i3ipc -- for i3 ipc interaction, installed from master
- toml -- to save/load human-readable configuration files.
- inotipy -- async inotify bindings
- Xlib -- xlib bindings to work with `NET_WM_` parameters, etc.
- ewmh -- used to create EWMH helper.
- yamlloader -- module for the more fast yaml file loading.
- pulsectl -- used for menu to change pulseaudio input / output sinks
- docopt -- for cli options in negi3wm script

To install it you may use pip:

```bash
sudo pip install -r requirements.txt --upgrade
```

or

```bash
sudo pip install --upgrade --force-reinstall git+git://github.com/acrisci/i3ipc-python@master \
    toml inotipy Xlib ewmh yamlloader pulsectl docopt
```

In case of pypy it may be something like

```bash
sudo pypy3 -m pip install --upgrade --force-reinstall git+git://github.com/acrisci/i3ipc-python@master \
    toml inotipy Xlib ewmh yamlloader pulsectl docopt
```

or

```bash
sudo pypy3 -m pip install -r requirements.txt --upgrade
```

etc. Of course you are also need pip or conda, or smth to install dependencies.

# Run

Install it to i3 config directory:

```bash
git clone https://github.com/neg-serg/negi3wm ~/.config/i3
```

negi3wm help:

```man
i3 negi3wm daemon script.

This module loads all negi3wm an start it via main's manager mailoop.
Inotify-based watchers for all negi3wm TOML-based configuration spawned here,
to use it just start it from any place without parameters.  Moreover it
contains pid-lock which prevents running several times.

Usage:
    ./negi3wm.py [--debug|--tracemalloc|--start]

Options:
    --debug         disables signal handlers for debug.
    --tracemalloc   calculates and shows memory tracing with help of
                    tracemalloc.
    --start         make actions for the start, not reloading
```

To start daemon you need:

```bash
cd ${XDG_CONFIG_HOME}/negi3wm
./negi3wm.py
```

but I recommend you to look at my config(\_config). It can start / restart
automatically, because of i3 connection will be closed after i3 restart and
then started by `exec_always`.

# Performance

## Performance profiling

You can check measure startup performance with tools like pycallgraph.

Also you can try

```bash
kernprof -l -v ./negi3wm.py
```

for the more detail function/line-based profiling. As far as I know PyPy3 is
not supported yet.

For now negi3wm using cpython interpreter because of more fast startup.

# Why

It is only my attempt to port the best UX parts from ion3/notion and also
improve it when possible. But if you try I may find that things, like better
scratchpad or navigation very useful.

# Bugs

For now here can be dragons, so add bug report to github if you get
problems.

# Video Demonstration

Youtube (low quality):
[![i3pluginsdemo](https://img.youtube.com/vi/U7eJMP0zvKc/0.jpg)](https://www.youtube.com/embed/U7eJMP0zvKc)

Vimeo (good quality):
[![i3pluginsdemovimeo](https://i.imgur.com/QIuWrkX.png)](https://vimeo.com/255452812)
