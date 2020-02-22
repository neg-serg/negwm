#!/bin/zsh
${XDG_CONFIG_HOME}/i3/negi3mods.py --start >> ${HOME}/tmp/negi3mods.log 2>&1 &
make -C ${XDG_CONFIG_HOME}/i3/ &
pkill -f 'mpc idle'
pkill sxhkd; sxhkd &
