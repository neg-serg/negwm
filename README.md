![banner](https://i.imgur.com/fgmuilL.png)

# Screenshots

![shot1](https://i.imgur.com/1cox0ps.png)

# What is it?

For now this collection of modules for i3 includes:

## main

*negi3mods* : application that run all modules and handle configuration of
ppi3+i3 and modules on python. Also handles TOML-configs updating.

## modules

*bscratch* : named ion3-like scratchpads with a whistles and fakes.

*win_history* : alt-tab to the previous window, not the workspace.

*circle* : better run-or-raise, with jump in a circle, subtags, priorities
and more.

*menu* : menu module including i3-menu with hackish autocompletion, menu to
attach window to window group(circled) or target named scratchpad(nsd) and
more. 

*vol*: contextual volume manager. Handles mpd by default. If mpd is
stopped then handles mpv with mpvc if the current window is mpv, or with
sending 0, 9 keys to the mpv window if not.

*win_action*: various stuff to emulate some 2bwm UX.

*executor*: module to create various terminal windows with custom config
and/or tmux session handling. Supports a lot of terminal emulators.

*fs*: fullscreen panel hacking. Works unstable, so disable it for now.

## procs to run by negi3mods as another process

~~There are processes, not threads, separated from the main negi3mods event
loop to reach better performance or another goals.~~

For now there are no any processes started by negi3mods. I've considered that
this scheme of loading can cause various race condictions and another
stability issues.

## procs to run from polybar

*polybar_ws*: async current i3 workspace printer for polybar.

*polybar_vol* : async MPD printer for polybar.

# Dependencies:

## Modern python3 with modules:

+ i3ipc -- for i3 ipc interaction, installed from master
+ toml -- to save/load human-readable configuration files.
+ inotify -- to reload configs in realtime without reloading.
+ aionotify -- async inotify bindings
+ aiofiles -- async file input-output
+ Xlib -- xlib bindings to work with `NET_WM_` parameters, etc.
+ ewmh -- used to create EWMH helper.
+ yamlloader -- module for the more fast yaml file loading.
+ pulsectl -- used for menu to change pulseaudio input / output sinks
+ docopt -- for cli options in negi3mods script


To install it you may use pip:

```
sudo pip install -r requirements.txt --upgrade
```

or

```
sudo pip install --upgrade --force-reinstall git+git://github.com/acrisci/i3ipc-python@master \
    inotify toml aionotify aiofiles Xlib \
    ewmh yamlloader pulsectl docopt
```

In case of pypy it may be something like

```
sudo pypy3 -m pip install --upgrade --force-reinstall git+git://github.com/acrisci/i3ipc-python@master \
    inotify toml aionotify aiofiles Xlib \
    ewmh yamlloader pulsectl docopt
```

or

```
sudo pypy3 -m pip install -r requirements.txt --upgrade
```

etc. Of course you are also need pip or conda, or smth to install dependencies.

Also you need [ppi3] as i3 config preprocessor.

# Run

To start daemon you need:

```
cd ${XDG_CONFIG_HOME}/i3
./negi3mods.py
```

but I recommend you to look at my config(_config). It can start / restart automatically,
because of i3 connection will be closed after i3 restart and then started by
`exec_always`.

# Performance

## Performance profiling

You can check measure startup performance with tools like pycallgraph.

Also you can try

```
kernprof -l -v ./negi3mods.py
```

for the more detail function/line-based profiling. As far as I know PyPy3 is
not supported yet.

For now negi3mods using cpython interpreter because of more fast startup.


# Why

It is only my attempt to port the best UX parts from ion3/notion and also improve
it when possible. But if you try I may find that things, like better
scratchpad or navigation very useful.

# Bugs

For now here can be dragons, so add bug report to github if you get
problems.

# Video Demonstration
Youtube (low quality):
[![i3pluginsdemo](https://img.youtube.com/vi/U7eJMP0zvKc/0.jpg)](https://www.youtube.com/embed/U7eJMP0zvKc)

Vimeo (good quality):
[![i3pluginsdemovimeo](https://i.imgur.com/QIuWrkX.png)](https://vimeo.com/255452812)

[ppi3]: https://github.com/KeyboardFire/ppi3
