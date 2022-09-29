i3-persist(1)
=============
[![Build Status](https://travis-ci.org/Igrom/i3-persist.svg?branch=master)](https://travis-ci.org/Igrom/i3-persist)

Name
----
i3-persist - extends i3 window management with persistent containers


Synopsis
--------
i3-persist lock|unlock|toggle|kill [\<id>]

Description
-----------
Closes a container or switches its state from closable to persistent.

Using the featured set of commands, containers can be marked so as to prevent their careless closing. A custom kill command is made available as a plug-in substitute for 'i3-msg kill'. If a container is marked as persistent, attempted closing of the container through the command will have no effect.

By default, i3-persist will operate on the currently focused container. For scripting purposes, it is possible to pass a con\_id to all methods.  

More information about the tool, as well as up-to-date information about the specific commands can be found in the man page found in the doc directory.

Installation notes
------------------
Package prerequisites:
- jq
- shunit2 (for unit testing)

1. Copy the repository to your machine.
2. (Optional) Run tests with `./run_tests.sh`.
3. Create a symlink to bin/i3-persist in your $PATH.
4. Copy the contents of the doc directory to a suitable directory (e.g., /usr/local/man or elsewhere along your $MANPATH, if variable exists).

The tool is the most convenient when used with keybindings.

Example .config/i3/config bindings:
- bindsym $mod+Shift+q exec 'i3-persist kill'
- bindsym $mod+Delete exec 'i3-persist toggle'

Copyright
---------
Copyright © 2018 Igor Sowinski.  Licensed under the 3-clause BSD license.
