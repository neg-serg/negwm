My nice and fast modules for i3.

# What is it?

For now this collection of modules for i3 includes:

*nsd* : named ion3-like scratchpads with a whistles and fakes.

*flastd* : alt-tab to the previous window, not the workspace.

*circled* : better run-or-raise, with jump in a circle, subgroups, priorities
and more.

*negi3mods* : application that run all modules and handle configuration of
ppi3+i3 and modules on python. Also handles toml-configs updating.

*menud* : menu module including i3-menu with hackish autocompletion, menu to
attach window to window group(circled) or target named scratchpad(nsd) and
more. 

*fsmpmsd* : module to disable dpms, when fullscreen mode are toggled on.

*infod* : module to extract info from running i3-mods via AF_INET socket.
For example it used to send information to the *polybar* as current workspace
or i3-binding mode because of native polybar i3-interaction tends to race
condition when you try to switch workspaces backward-forward to quickly.

*vold* : contextual volume manager. Handles mpd by default. If mpd is stopped
then handles mpv with mpvc if the current window is mpv, or with sending 0,
9 keys to the mpv window if not.

Many of them as circled, infod, nsd, vold, wm3d can be configured via
TOML-files with inotify-based autoreload.

# Dependencies:

## Modern python3 with modules:

1) i3ipc -- for i3 ipc interaction.
2) toml -- to save/load human-readable configuration files.
3) inotify -- to reload configs in realtime without reloading.
4) gevent -- for the mainloop queue, greenlets.

To install it you may use pip:

```
pip install inotify
pip install gevent
pip install i3ipc
pip install toml
```

In case of pypy it may be something like

```
pypy3 -m pip install gevent
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
better on my machine. You can check measure performance with tools like pycallgraph.~~

*Upd*: for some reason with stackless python I've got not correct return for
`focused.workspace().descendents()` case, maybe it's my fault, but I can't
fix that. As the result the nsd.py behaviour is not always corrent for now
with stackless python 3.6 or 3.7, but ok with `CPython 3.6`.

It seems that for now `pypy3 5.10.1-1` works very nice. Maybe this is because
of code changes over the time.

# Why

It is only my attempt to port the best UX parts from ion3/notion and also improve
it when possible. But if you try I may find that things, like better
scratchpad or navigation very useful.

# Bugs

For now here can be dragons, so add bug report to github if you get
problems.

# Video Demonstration
[![i3pluginsdemo](https://img.youtube.com/vi/U7eJMP0zvKc/0.jpg)](https://www.youtube.com/embed/U7eJMP0zvKc)

[ppi3]: https://github.com/KeyboardFire/ppi3
