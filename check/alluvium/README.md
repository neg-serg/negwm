# alluvium - interactive bindings visualizer for i3

alluvium guides you through your keybindings and modes in i3 as you enter them. It is
heavily inspired by [remontoire](https://github.com/regolith-linux/remontoire) and reuses
its comment syntax in the `i3/config` file to learn about keybindings, modes and their
description.

| Default overlay                             | After entering Settings mode                 | After entering Session mode                 |
|---------------------------------------------|----------------------------------------------|---------------------------------------------|
| ![Overlay](screenshots/default-overlay.png) | ![Overlay](screenshots/settings-overlay.png) | ![Overlay](screenshots/session-overlay.png) |

## Usage

Install alluvium, for example via `pip install alluvium`, and run it manually. It will
connect to i3 and show your bindings - if you put remontoire annotations into your config.

To use alluvium in i3, ensure that the `alluvium` executable is callable by i3. So if you
installed it in pyenv, you might need to put a symlink to `$(pyenv which alluvium)` into
your `.local/bin`, so that i3 can find the executable without knowing about pyenv.

```
## Launch // Toggle alluvium // <> ? ##
bindsym $mod+Shift+question $run alluvium --toggle

## Settings // Enter Settings Mode // <> F11 ##
mode "Settings" {
    ## Settings // Control Center // c ##
    bindsym c exec gnome-control-center; mode "default"

    ## Settings // Display // d ##
    bindsym d exec gnome-control-center display; mode "default"

    ## Settings // Wifi // w ##
    bindsym w exec gnome-control-center wifi; mode "default"

    ## Settings // Bluetooth // b ##
    bindsym b exec gnome-control-center bluetooth; mode "default"

    ## Settings // Exit Settings Mode // Escape or <Ctrl> g ##
    bindsym Escape mode "default"
    bindsym Ctrl+g mode "default"
}
bindsym $mod+F11 mode "Settings"; $run alluvium --mode Settings --quit-on-default
```

The first binding toggles the overlay while the binding to `$mod+F11` enters the settings
mode with an overlay showing the bindings available in that mode. `--quit-on-default`
makes the overlay disappear when you return to default mode. This is most helpful for
rarely used modes such as system settings as above or a mode to manage i3 itself.

## Syntax

The config syntax is the same as in remontoire, that is

```
## <Group> // <Label> // <Keys> ##
```

with an extension to define modes. If a group contains a binding with a label of `Enter
... Mode`, alluvium recognizes the group as a mode. The enter binding shows up in the
`Modes` group in the top level display while the other bindings of the group are shown
when you enter the mode.

## Arch Linux

+ Package created as: `alluvium-git`

Install with your favorite pacman helper (`yay`,`pikaur`,`trizen`, etc).  
`$ yay|pikaur|trizen -S alluvium-git`
