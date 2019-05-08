""" Matcher module

In this class to check that window can be tagged with given tag by
WM_CLASS, WM_INSTANCE, regexes, etc. It can be used by named scrachpad,
circle run-or-raise, etc.
"""

import sys
import re
from typing import List, Iterator


class Matcher(object):
    """ Generic matcher class

    Used by several classes. It can match windows by several criteria, which
    I am calling "factor", including:
        - by class, by class regex
        - by instance, by instance regex
        - by role, by role regex
        - by name regex

    Of course this list can by expanded. It uses sys.intern hack for better
    performance and simple caching. One of the most resource intensive part of
    negi3mods.

    """

    def __init__(self):
        self.factors = [
            sys.intern("class"),
            sys.intern("instance"),
            sys.intern("role"),
            sys.intern("class_r"),
            sys.intern("instance_r"),
            sys.intern("name_r"),
            sys.intern("role_r"),
            sys.intern('match_all')
        ]

        self.match_dict = {
            sys.intern("class"): lambda: self.win.window_class in self.matched_list,
            sys.intern("instance"): lambda: self.win.window_instance in self.matched_list,
            sys.intern("role"): lambda: self.win.window_role in self.matched_list,
            sys.intern("class_r"): self.class_r,
            sys.intern("instance_r"): self.instance_r,
            sys.intern("role_r"): self.role_r,
            sys.intern("name_r"): self.name_r,
            sys.intern("match_all"): self.match_all
        }

    def find_classed(self, win: List, pattern: str) -> Iterator:
        return (c for c in win
                if c.window_class and re.search(pattern, c.window_class))

    def find_instanced(self, win: List, pattern: str) -> Iterator:
        return (c for c in win
                if c.window_instance and re.search(pattern, c.window_instance))

    def find_by_role(self, win: List, pattern: str) -> Iterator:
        return (c for c in win
                if c.window_role and re.search(pattern, c.window_role))

    def find_named(self, win: List, pattern: str) -> Iterator:
        return (c for c in win if c.name and re.search(pattern, c.name))

    def class_r(self) -> bool:
        for pattern in self.matched_list:
            cls_by_regex = self.find_classed([self.win], pattern)
            if cls_by_regex:
                for class_regex in cls_by_regex:
                    if self.win.window_class == class_regex.window_class:
                        return True
        return False

    def instance_r(self) -> bool:
        for pattern in self.matched_list:
            inst_by_regex = self.find_instanced([self.win], pattern)
            if inst_by_regex:
                for inst_regex in inst_by_regex:
                    if self.win.window_instance == inst_regex.window_instance:
                        return True
        return False

    def role_r(self) -> bool:
        for pattern in self.matched_list:
            role_by_regex = self.find_by_role([self.win], pattern)
            if role_by_regex:
                for role_regex in role_by_regex:
                    if self.win.window_role == role_regex.window_role:
                        return True
        return False

    def name_r(self) -> bool:
        for pattern in self.matched_list:
            name_by_regex = self.find_named([self.win], pattern)
            if name_by_regex:
                for name_regex in name_by_regex:
                    if self.win.name == name_regex.name:
                        return True
        return False

    def match_all(self) -> bool:
        return True

    def match(self, win, tag: str) -> bool:
        self.win = win

        for f in self.factors:
            self.matched_list = self.cfg.get(tag, {}).get(f, {})
            if self.matched_list and self.match_dict[f]():
                return True
        return False

