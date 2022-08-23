#!/usr/bin/env python3

import sys
import errno
import argparse
import config as config
import keys

# Hardcoded default variable for the primary modifier key,
# can be changed with --modvar
modVariable = "Mod4"

# The keys that will be listed as available
keys = keys.getKeys(
    ["0-9", "a-z", "nordic", "arrow", "common", "function"])

def printAvailable(modifier, available):
    """Prints available keys and their modifiers

    :param modifier: list of modifiers
    :type modifier: dict
    :param available: list of available keys, see config.Config.availableBindings()
    :type available: list
    """

    mods = "+".join([m for m in modifier])
    print("\nAvailable " + mods + ":")
    print(", ".join(available))

# Init argparse
parser = argparse.ArgumentParser(
    description="Lists available bindings for i3.")
parser.add_argument(
    "--modvar", help="variable name of modkey, e.g. '$m', defaults to $mod", type=str)
parser.add_argument(
    "--config", help="path to configuration file. Otherwise it searches in default locations.", type=str)
parser.add_argument(
    "-m", "--mod", help="available $mod bindings", action="store_true")
parser.add_argument(
    "-s", "--shift", help="available $mod+Shift bindings", action="store_true")
parser.add_argument(
    "-c", "--ctrl", help="available $mod+Ctrl bindings", action="store_true")
parser.add_argument(
    "-t", "--triplet", help="available $mod+Ctrl+Shift bindings", action="store_true")
parser.add_argument(
    "-b", "--bindings", help="custom binding(s), e.g. '$mod+Mod2'", type=str, nargs='+')
args = parser.parse_args()

# Turple with args that will be iterated
boolArgs = ("mod", "shift", "ctrl", "triplet")

# If --modvar is set change the default modifier
if args.modvar:
    modVariable = args.modvar

combinations = {
    "mod": [modVariable],
    "shift": [modVariable, "Shift"],
    "ctrl": [modVariable, "Ctrl"],
    "triplet": [modVariable, "Ctrl", "Shift"],
}

# Adds custom binding(s)
if args.bindings:
    for i, b in enumerate(args.bindings):
        combinations["binding_"+str(i)] = b.split("+")

# Use user selected config else search defaults
if args.config:
    conf = config.Path(args.config)
    if conf.exists == False:
        print("Error: Couldn't find or read the i3 configuration file", file=sys.stderr)
        sys.exit(errno.ENOENT)
else:
    configs = [
        config.Path("~/.i3/config"),
        config.Path("/i3/config", "XDG_CONFIG_HOME"),
        config.Path("~/.config/i3/config"),
        config.Path("/etc/i3/config"),
        config.Path("/i3/config", "XDG_CONFIG_DIRS"),
        config.Path("/etc/xdg/i3/config"),
    ]
    conf = None
    for c in configs:
        if c.exists:
            conf = c
            break
    if conf == None:
        print("Error: Couldn't find or read any i3 configuration file", file=sys.stderr)
        sys.exit(errno.ENOENT)

print(f"Reading from {conf.path}")
c = config.Config(conf.path)

# Checks if atleast one keygroup is selected, else all True
if not args.bindings and not any([getattr(args, x) for x in boolArgs]):
    for attr in combinations:
        setattr(args, attr, True)

# Iterate through arguments and print if selected
for attr in combinations:
    # Skip combinations that isn't selected by the user
    if attr in args and not getattr(args, attr):
        continue
    available = c.availableBindings(keys, combinations[attr])
    printAvailable(combinations[attr], available)

# # I recommend you check out my new program [i3keys](https://github.com/RasmusLindroth/i3keys) instead
#
# You are still free to use i3av if you like, but I will prioritize i3keys.
#
# # i3av(ailable)
#
# This Python3 script list keys that isn't being used by i3 as keybindings so you
# easier can find available keys.
# You can limit the listing to selected modifier keys and
# specify the path to the configuration file, see [help](#help).
#
# * [Getting started](#getting-started)
#   * [Change keys to list as available](#change-keys-to-list-as-available)
#   * [Change primary modifier key](#change-primary-modifier-key)
#   * [Custom bindings](#custom-bindings)
# * [Example](#example)
# * [Help](#help)
#
# ### Getting started
# ````bash
# # Clone this repo and go to the directory
# git clone https://github.com/RasmusLindroth/i3av.git
# cd i3av/
#
# # Run the program
# ./i3av.py
# ````
#
# #### Change keys to list as available
#
# If you would like to change which keys that get listed you can
# edit [i3av.py](./i3av.py) and [lib/keys.py](./lib/keys.py).
#
# In [i3av.py](./i3av.py) you have a line like this:
#
# ````Python
# keys = lib.keys.getKeys(
#     ["0-9", "a-z", "nordic", "arrow", "common", "function"])
# ````
#
# Current possible keys are `0-9, a-z, nordic, arrow, common, uncommon, function,
# numpad, numpad_other`
#
# If you want to add more keys, just add your keys in the dict `keys = {...}`
# located in [lib/keys.py](./lib/keys.py).
#
# #### Change primary modifier key
#
# This script defaults to `$mod` as the modifier key. You can change this with
# adding the argument `--modvar '$m'` or change `modVariable` in [i3av.py](./i3av.py).
#
# #### Custom bindings
#
# If the modifiers provided isn't enough you can add your own with `--bindings`,
# e.g. `./i3av.py --bindings '$mod+Mod2' '$mod+Mod4'`. You can also change the
# code, take a look at the dict `combinations` in [i3av.py](./i3av.py).
#
# ### Example
#
# ````bash
# $ ./i3av.py -m
# Reading from /home/rasmus/.i3/config
#
# Available $mod:
# g, i, o, p, x, oslash, ae, BackSpace, Tab, Pause, Scroll_Lock, Escape, Delete,
# Prior, Next, End, Insert, Menu, Break, comma, period, slash, semicolon,
# backslash, bracketleft, bracketright, plus, equal, less, greater, apostrophe,
# asterisk, grave, section, F1, F4, F6, F7, F8, F9, F10, F11, F12
# ````
#
# ### Help
# ````bash
# ./i3av.py --help
# usage: i3av.py [-h] [--modvar MODVAR] [--config CONFIG] [-m] [-s] [-c] [-t]
#                [-b BINDINGS [BINDINGS ...]]
#
# Lists available bindings for i3.
#
# optional arguments:
#   -h, --help            show this help message and exit
#   --modvar MODVAR       variable name of modkey, e.g. '$m', defaults to $mod
#   --config CONFIG       path to configuration file. Otherwise it searches in
#                         default locations.
#   -m, --mod             available $mod bindings
#   -s, --shift           available $mod+Shift bindings
#   -c, --ctrl            available $mod+Ctrl bindings
#   -t, --triplet         available $mod+Ctrl+Shift bindings
#   -b BINDINGS [BINDINGS ...], --bindings BINDINGS [BINDINGS ...]
#                         custom binding(s), e.g. '$mod+Mod2'
