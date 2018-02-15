My nice and fast modules for i3.

# Dependencies:

* i3ipc
* ppi3 as i3 config preprocessor.
* modern i3 python with modules:

-- i3ipc
-- shlex
-- subprocess
-- toml
-- typing
-- uuid

# What is it?

*nsd* : named ion3-like scratchpads with a whistles and fakes.
*flastd* : alt-tab to the previous window, not the workspace.
*circled* : better run-or-raise, with jump in a circle, subgroups, priorities
and more.

*nsd* and *circled* can be configured over toml files with inotify-based
autoreload.

*listner* : application that run all modules and handle configuration of
ppi3+i3 and modules on python. Also handles toml-configs updating.
