My nice and fast modules for i3.

# Dependencies:

* i3ipc
* ppi3 as i3 config preprocessor.
* modern python3(stackless python3 is preferred) with modules:

- i3ipc
- shlex
- subprocess
- toml
- typing
- uuid

I recommend you to use stackless python for better performance. Nuitka / pypy
/ cython are not the best choise here: native python3 performance looks
better on my machine. For example you can check it with pycallgraph.

# What is it?

*nsd* : named ion3-like scratchpads with a whistles and fakes.
*flastd* : alt-tab to the previous window, not the workspace.
*circled* : better run-or-raise, with jump in a circle, subgroups, priorities
and more.

*nsd* and *circled* can be configured over toml files with inotify-based
autoreload.

*listner* : application that run all modules and handle configuration of
ppi3+i3 and modules on python. Also handles toml-configs updating.

# Video Demonstration
[![i3pluginsdemo](https://img.youtube.com/vi/U7eJMP0zvKc/0.jpg)](https://www.youtube.com/embed/U7eJMP0zvKc)
