# New
    - Dynamic workspaces with circle integration
    - Mouse helper, for example get windows size and then click on x,y = 20px, 20px

# General
    - Create PKGBUILD
    - Make post on usability porn reddit
    - Percent resize, move to some region subtle like semi-dynamic tiling / dwm-like tiling
    - Remove all default parameters and add config validation

# Config
    - Better generator(fancy output, etc)

# Scratchpad
    - Add ability to set geometry with mouse
    - Add labels support print scratchpad names
    - Set geometry for scratchpad windows(optional)

# Menu
    - Fix ex-gnome module
    - Add stuff for marks add del to attach to ws, etc

# Experiments
    - ./bin/i3gw top; i3-msg '[con_mark=top] resize set 30 ppt'
    - Better dynamic config architecture
    - Python reload dynamic
    • default config: use dex for XDG autostart
    • docs/ipc: document scratchpad_state
    • ipc: the GET_CONFIG request now returns all included files and their details
    # Start XDG autostart .desktop files using dex. See also
    # https://wiki.archlinux.org/index.php/XDG_Autostart
    exec --no-startup-id dex --autostart --environment i3
    exec --no-startup-id xss-lock --transfer-sleep-lock -- i3lock --nofork
    bindsym Mod1+s layout stacking
    bindsym Mod1+w layout tabbed
    bindsym Mod1+e layout toggle split
    bindsym Mod1+Shift+space floating toggle
    bindsym Mod1+space focus mode_toggle
    # focus the parent container
    bindsym Mod1+a focus parent
