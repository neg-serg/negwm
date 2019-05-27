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

    factors = [
        sys.intern("class"),
        sys.intern("instance"),
        sys.intern("role"),
        sys.intern("class_r"),
        sys.intern("instance_r"),
        sys.intern("name_r"),
        sys.intern("role_r"),
        sys.intern('match_all')
    ]

    def __init__(self):
        self.matched_list = []

        self.match_dict = {
            sys.intern("class"): lambda: self.win.window_class in self.matched_list,
            sys.intern("instance"): lambda: self.win.window_instance in self.matched_list,
            sys.intern("role"): lambda: self.win.window_role in self.matched_list,
            sys.intern("class_r"): self.class_r,
            sys.intern("instance_r"): self.instance_r,
            sys.intern("role_r"): self.role_r,
            sys.intern("name_r"): self.name_r,
            sys.intern("match_all"): Matcher.match_all
        }

    @staticmethod
    def find_classed(win: List, pattern: str) -> Iterator:
        """ Returns iterator to find by window class """
        return (c for c in win
                if c.window_class and re.search(pattern, c.window_class))

    @staticmethod
    def find_instanced(win: List, pattern: str) -> Iterator:
        """ Returns iterator to find by window instance """
        return (c for c in win
                if c.window_instance and re.search(pattern, c.window_instance))

    @staticmethod
    def find_by_role(win: List, pattern: str) -> Iterator:
        """ Returns iterator to find by window role """
        return (c for c in win
                if c.window_role and re.search(pattern, c.window_role))

    @staticmethod
    def find_named(win: List, pattern: str) -> Iterator:
        """ Returns iterator to find by window name """
        return (c for c in win if c.name and re.search(pattern, c.name))

    def class_r(self) -> bool:
        """ Check window by class with regex """
        for pattern in self.matched_list:
            cls_by_regex = Matcher.find_classed([self.win], pattern)
            if cls_by_regex:
                for class_regex in cls_by_regex:
                    if self.win.window_class == class_regex.window_class:
                        return True
        return False

    def instance_r(self) -> bool:
        """ Check window by instance with regex """
        for pattern in self.matched_list:
            inst_by_regex = Matcher.find_instanced([self.win], pattern)
            if inst_by_regex:
                for inst_regex in inst_by_regex:
                    if self.win.window_instance == inst_regex.window_instance:
                        return True
        return False

    def role_r(self) -> bool:
        """ Check window by role with regex """
        for pattern in self.matched_list:
            role_by_regex = Matcher.find_by_role([self.win], pattern)
            if role_by_regex:
                for role_regex in role_by_regex:
                    if self.win.window_role == role_regex.window_role:
                        return True
        return False

    def name_r(self) -> bool:
        """ Check window by name with regex """
        for pattern in self.matched_list:
            name_by_regex = Matcher.find_named([self.win], pattern)
            if name_by_regex:
                for name_regex in name_by_regex:
                    if self.win.name == name_regex.name:
                        return True
        return False

    @staticmethod
    def match_all(self) -> bool:
        """ Match every possible window """
        return True

    def match(self, win, tag: str) -> bool:
        """ Check that window matches to the config rules """
        self.win = win

        for f in Matcher.factors:
            self.matched_list = self.cfg.get(tag, {}).get(f, {})
            if self.matched_list and self.match_dict[f]():
                return True
        return False

