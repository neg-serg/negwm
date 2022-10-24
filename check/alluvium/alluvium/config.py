import itertools
from collections import namedtuple

import re


class Config:
    Keybinding = namedtuple("Keybinding", ["group", "label", "keys"])
    REMONTOIRE_ANNOTATION = re.compile(
        r"^\s*##([^#/]*)//([^#/]*)//([^#/]*)##", re.MULTILINE
    )

    def __init__(self, groups, modes):
        self.groups = groups
        self.modes = modes

    @classmethod
    def from_data(cls, data):
        def enters_mode(binding):
            label = binding.label
            return label.startswith("Enter ") and label.endswith(" Mode")

        bindings = cls.parse_config(data)
        all_groups = [
            (group, list(bs))
            for group, bs in itertools.groupby(bindings, lambda b: b.group)
        ]
        groups = []
        modes = []
        for group, bs in all_groups:
            if any(enters_mode(b) for b in bs):
                modes.append((group, bs))
            else:
                groups.append((group, bs))
        mode_group = ("Modes", [])
        for mode, bindings in modes:
            enters = [b for b in bindings if enters_mode(b)]
            mode_group[1].extend(enters)
            for b in enters:
                bindings.remove(b)
        groups.append(mode_group)

        return cls(groups, modes)

    @staticmethod
    def parse_keys(spec):
        keys = []
        i = 0
        while i < len(spec):
            if spec[i] == "<":
                closing = spec.find(">", i + 1)
                if closing == -1:
                    raise Exception(f"Unmatched < in keybinding {spec}")
                else:
                    keys.append(spec[(i + 1) : closing])
                    i = closing + 1
            elif spec[i] == " ":
                i += 1
            else:
                next_space = spec.find(" ", i + 1)
                if next_space == -1:
                    keys.append(spec[i:])
                    break
                else:
                    keys.append(spec[i:next_space])
                    i = next_space

        return keys

    @staticmethod
    def parse_config(data):
        return [
            Config.Keybinding(m[0].strip(), m[1].strip(), Config.parse_keys(m[2]))
            for m in Config.REMONTOIRE_ANNOTATION.findall(data)
        ]
