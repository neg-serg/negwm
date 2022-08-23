#!/usr/bin/env python3

import os
import re
import subprocess


def getKeyCodes():
    """Get keycodes from xmodmap with the corresponding keysym

    :return: A dictionary with keycode as key and keysym as value
    :rtype: dict or False
    """

    keycodes = {}
    reKeycode = re.compile(
        r"^keycode\s*(\d+?)\s*=\s*(?:NoSymbol\s?)*(.+?)(?:\s+|$)")
    try:
        ls = subprocess.Popen(['xmodmap', '-pke'], stdout=subprocess.PIPE)
        for line in ls.stdout:
            l = line.decode().strip()
            matches = reKeycode.match(l)

            if matches:
                keycodes[matches.group(1)] = matches.group(2)
    except FileNotFoundError:
        print("Warning: Could't call xmodmap. Keycodes will not be mapped to keysyms.")
        return False
    return keycodes


class Path:
    """Holds a path to an i3 configuration file and checks if it exists
    """

    def __init__(self, path, env=""):
        """Init path

        :param path: path to i3 config
        :type path: str
        :param env: environment variable that prepends path e.g. "XDG_CONFIG_HOME", defaults to ""
        :param env: str, optional
        """

        if env == "":
            self.path = self.getPath(path)
            self.exists = self.checkPath()
        elif env != "" and env in os.environ:
            self.path = self.getPath(os.environ[env] + path)
            self.exists = self.checkPath()
        else:
            self.path = None
            self.exists = False

    def getPath(self, path):
        """Expands tilde to home path

        :param path: path to config
        :type path: str
        :return: expanded path
        :rtype: str
        """
        return os.path.expanduser(path)

    def checkPath(self):
        """Check if the file exists and if we can read it

        :return: bool
        :rtype: bool
        """

        if os.path.isfile(self.path) and os.access(self.path, os.R_OK):
            return True
        return False


class Config:
    """Holds a configuration file and the keybindings in it
    """

    def __init__(self, path):
        """Init config

        :param path: path to configuration file
        :type path: str
        """

        self.path = path
        self.variables = self.parseVariables()
        self.bindings = self.parseBindings()

    def readConfig(self):
        with open(self.path, "r") as f:
            for line in f:
                l = line.strip()
                yield l

    def parseVariables(self):
        """Parses variables that are set in the config and saves them

        :return: A dict with varName: value
        :rtype: dict
        """

        reSet = re.compile(r"^set\s+(\$.+?)\s+(.+?)$")
        variables = {}
        for line in self.readConfig():
            matches = reSet.match(line)
            if matches:
                variables[matches.group(1)] = matches.group(2)
        return variables

    def parseBindings(self):
        """Gets keybindings from configuration file

        :return: a list of keybindings, [Binding, ...]
        :rtype: list
        """

        reBinding = re.compile(r"^bind(sym|code)\s(.+?)\s")
        bindings = []

        for line in self.readConfig():
            matches = reBinding.match(line)
            if matches:
                bindings.append(
                    Binding(
                        matches.group(1), matches.group(2), self.variables
                    )
                )
        return bindings

    def availableBindings(self, keys, combination):
        """Check which keybindings that aren't used for selected modifiers

        :param keys: list of keys e.g. ["a","1","Escape"]
        :type keys: list
        :param combination: dict of modifiers to compare with
        :type combination: dict
        :return: a list of available keybindings, bindings that isn't used
        :rtype: list
        """
        newComb = set()

        for c in combination:
            # if variable, replace it with the right value
            if c in self.variables:
                newComb.add(self.variables[c])
            else:
                newComb.add(c)

        used = [x.sym.lower()
                for x in self.bindings if set(x.modifiers) == newComb and x.sym != None]
        return [x for x in keys if x.lower() not in used]


class Binding:
    """Holds a keybinding
    """

    def __init__(self, bindtype, keys, variables):
        """Init Binding

        :param bindtype: either sym or code
        :type bindtype: str
        :param keys: string of keys, e.g. "$mod+Shift+a"
        :type keys: str
        :param variables: a dict with variables
        :type variables: dict
        """

        self.type = bindtype
        self.sym = None
        self.code = None

        self.modifiers = []
        splitted = self.splitKeys(keys)
        self.keys = self.expandVars(splitted, variables)
        self.setModifiers()

        if self.type == "sym" and len(self.keys) > 0:
            self.sym = self.keys[-1]
        elif self.type == "code" and len(self.keys) > 0:
            self.code = self.keys[-1]
            self.sym = self.getKeySym(self.code)

    def expandVars(self, keys, variables):
        """Expands variable to their corresponding value

        :param keys: a list of keys
        :type keys: list
        :param variables: a dict with variables
        :type variables: dict
        :return: a list with keys, expanded variables
        :rtype: list
        """

        r = []
        for k in keys:
            if k in variables:
                r.append(variables[k])
            else:
                r.append(k)
        return r

    def splitKeys(self, keys):
        """Splits a string of keys to a list

        :param keys: string of keys, e.g. "$mod+Shift+a"
        :type keys: str
        :return: returns a list of keys, e.g. ["$mod", "Shift", "a"]
        :rtype: list
        """

        return [x for x in keys.split("+")]

    def setModifiers(self):
        """Adds all modifiers to a list
        """

        for k in self.keys[:-1]:
            self.modifiers.append(k)

    def getKeySym(self, code):
        """Keycode to keysym

        :param code: Keycode
        :type code: str
        :return: Keysym
        :rtype: str or None
        """

        if keycodes != False and code in keycodes:
            return keycodes[code]
        else:
            return None

    def __str__(self):
        """String representation of object

        :return: a string of the keybinding
        :rtype: str
        """

        v = []
        for m in self.modifiers:
            v.append(m)
        v.append(self.sym or "(code " + self.code + ")")
        return "+".join(v)


keycodes = getKeyCodes()
