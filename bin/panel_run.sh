#!/bin/dash
export POLYBAR_INPUT_FORMAT="input:%layout%"
export POLYBAR_LL="%{F-}"
export POLYBAR_RR="%{F-}"

pkill -x polybar
if [ $(pgrep -x polybar|wc -l) -le 1  ]; then
    polybar -c ${XDG_CONFIG_HOME}/polybar/main main &
fi
