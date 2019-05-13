![banner](https://i.imgur.com/fgmuilL.png)

# Screenshots

![shot1](https://i.imgur.com/1cox0ps.png)

# What is it?

For now this collection of modules for i3 includes:

## main

*negi3mods* : application that run all modules and handle configuration of
ppi3+i3 and modules on python. Also handles TOML-configs updating.

## modules

*better_scratchpad* : named ion3-like scratchpads with a whistles and fakes.

*win_history* : alt-tab to the previous window, not the workspace.

*circle* : better run-or-raise, with jump in a circle, subtags, priorities
and more.

*menu* : menu module including i3-menu with hackish autocompletion, menu to
attach window to window group(circled) or target named scratchpad(nsd) and
more. 

*vol*: contextual volume manager. Handles mpd by default. If mpd is
stopped then handles mpv with mpvc if the current window is mpv, or with
sending 0, 9 keys to the mpv window if not.

*wm3*: various stuff to emulate some 2bwm UX.

*executor*: module to create various terminal windows with custom config
and/or tmux session handling. Supports a lot of terminal emulators.

## procs to run by negi3mods as another process

There are processes, not threads, separated from the main negi3mods event
loop to reach better performance or another goals.

*info* : module to extract info from running i3-mods via `AF_INET6` socket.
For example it used to send information to the *polybar* as current workspace
or i3-binding mode because of native polybar i3-interaction tends to race
condition when you try to switch workspaces backward-forward to quickly.
Can be used as helper for another modules, like `polybar_ws`.

*fs* : module to disable dpms, when fullscreen mode are toggled on. Also it
handles polybar show / hide to mimic ion3 default fullscreen behaviour.

## procs to run from polybar

*polybar_ws*: async current i3 workspace printer for polybar.

*polybar_vol* : async MPD printer for polybar.

# Dependencies:

## Modern python3 with modules:

+ i3ipc -- for i3 ipc interaction.
+ toml -- to save/load human-readable configuration files.
+ inotify -- to reload configs in realtime without reloading.
+ aionotify -- async inotify bindings
+ aiofiles -- async file input-output


To install it you may use pip:

```
sudo pip install -r requirements.txt --upgrade
```

or

```
sudo pip install --upgrade --force-reinstall inotify i3ipc toml aionotify aiofiles
```

In case of pypy it may be something like

```
sudo pypy3 -m pip install --upgrade --force-reinstall inotify i3ipc toml aionotify aiofiles
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

~~I recommend you to use *stackless python* for better performance. Nuitka / pypy
/ cython are *not* the best choise here: native python3 performance looks
better on my machine.~~

*Upd*: for some reason with stackless python I've got not correct return for
`focused.workspace().descendents()` case, maybe it's my fault, but I can't
fix that. As the result the nsd.py behaviour is not always corrent for now
with stackless python 3.6 or 3.7, but ok with `CPython 3.6`.

It seems that for now `pypy3 5.10.1-1` works very nice. Maybe this is because
of code changes over the time.

# Performance profiling

You can check measure startup performance with tools like pycallgraph.

Also you can try

```
kernprof -l -v ./negi3mods.py
```

for the more detail function/line-based profiling. As far as I know Pypy3 is
not supported yet.


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
