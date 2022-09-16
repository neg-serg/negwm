# i3parse
A functional but not feature-complete parser for [i3wm's](https://github.com/i3/i3) config file. Originally written for the purposes of querying keybindings, but it can likely be patched to support new features. These tools may be profitably combined with tools like [rofi](https://github.com/DaveDavenport/rofi) in keybindings for self-documentation.

# Installation
```
pip3 install --upgrade git+https://github.com/talwrii/i3parse#egg=i3parse
```

Requires Python3 but can coexist on a machine with Python 2.

# Usage
```
# List keybindings
> i3parse bindings

# Draw a graph of keybinding modes (for graphviz)
> i3parse mode-graph

# Show free keybindings
> i3parse free

# Show free keybindings containing a letter in "layout"
> i3parse free layout

# Show free keybindings that use shift
> i3parse free --shift

```

# Caveats
This code is a violation of [don't repeat yourself](http://wiki.c2.com/?DontRepeatYourself).
i3 defines a specification for its configuration file in [its source code](https://github.com/mariusmuja/i3wm/blob/dfcc65ab8dd8ff9b995c8f970424454342f8be2e/parser-specs/config.spec); we duplicate a different specification here which is liable to be invalidated by changes to i3's specification.
The author deemed that parsing this file (which is in a custom language that is parsed by a custom PERL script) was more effort that the costs of dealing with duplication, given that the configuration file is unlikely to change.

This parser was derived from features in the author's configuration file, rather than from i3's configuration file specification. As such, it may fail to parse your configuration but can likely quickly be patched to support new features.

# Debugging
In the case of parse errors, the author has found it helpful to copy the error-causing configuration and repeatedly delete lines until a minimal error-causing configuration is found. The grammar rules can then be reordered so that the most specific rule that should match is being used (the first rule in the grammar definition is the rule that the input file should match). Rules can further be commented out with `#` and replaced with even simpler rules. Having such a minimised problem helps one debug.

`python setup.py test` runs a test suite.

# Attribution and prior work
* This tool was very much influenced by [emacs](https://www.gnu.org/software/emacs/) with its features for self documentation.
* The [parsimonious library](https://github.com/erikrose/parsimonious) is used for parsing.
* [i3wm question regarding programmatically querying keybinding ](https://faq.i3wm.org/question/5483/how-can-i-list-all-xorg-and-i3-keybindings-currently-in-effect/index.html)
* The functionality to find unbound keys is influenced by a similar feature in emacs [free-keys](https://github.com/Fuco1/free-keys)
