""" Module to convert from 16:10 1080p geometry to target screen geometry.

    This module contains geometry converter and also i3-rules generator. Also
    in this module geometry is parsed from config X11 internal format to the i3
    commands.
"""

import re
from typing import List
from main import get_screen_resolution


class geom():
    def __init__(self, cfg: dict) -> None:
        """ Init function

        Args:
            cfg: config bypassed from target module, nsd for example.
        """
        # generated command list for i3 config
        self.cmd_list = []

        # geometry in the i3-commands format.
        self.parsed_geom = {}

        # set current screen resolution
        self.current_resolution = get_screen_resolution()

        # external config
        self.cfg = cfg

        # fill self.parsed_geom with self.parse_geom function.
        for tag in self.cfg:
            self.parsed_geom[tag] = self.parse_geom(tag)

    def scratchpad_hide_cmd(self, hide: bool) -> str:
        """ Returns cmd needed to hide scratchpad.

            Args:
                hide (bool): to hide target or not.
        """
        ret = ""
        if hide:
            ret = ", [con_id=__focused__] scratchpad show"
        return ret

    def ret_info(self, tag: str, attr: str, target_attr: str,
                 dprefix: str, hide: str) -> str:
        """ Create rule in i3 commands format

        Args:
            tag (str): target tag.
            attr (str): tag attrubutes.
            target_attr (str): attribute to fill.
            dprefix (str): rule prefix.
            hide (str): to hide target or not.
        """
        if target_attr in attr:
            lst = [item for item in self.cfg[tag][target_attr] if item != '']
            if lst != []:
                pref = dprefix+"[" + '{}="'.format(attr) + \
                    self.ch(self.cfg[tag][attr], '^')
                for_win_cmd = pref + self.parse_attr(tag, target_attr) + \
                    "move scratchpad, " + self.get_geom(tag) \
                                        + self.scratchpad_hide_cmd(hide)
                return for_win_cmd
        return ''

    def ch(self, lst: List, ch: str) -> str:
        """ Return char is list is not empty to prevent stupid commands.
        """
        ret = ''
        if len(lst) > 1:
            ret = ch
        return ret

    def parse_attr(self, tag: str, attr: str) -> str:
        """ Create attribute matching string.
            Args:
                tag (str): target tag.
                attr (str): target attrubute.
        """
        ret = ''
        attrib_list = self.cfg[tag][attr]
        if len(attrib_list) > 1:
            ret += '('
        for iter, item in enumerate(attrib_list):
            ret += item
            if iter+1 < len(attrib_list):
                ret += '|'
        if len(attrib_list) > 1:
            ret += ')$'
        ret += '"] '

        return ret

    def create_i3_match_rules(self, hide: bool = True,
                              dprefix: str = "for_window ") -> None:
        """ Create i3 match rules for all tags.

        Args:
            hide (bool): to hide target or not, optional.
            dprefix (str): i3-cmd prefix is "for_window " by default, optional.
        """
        cmd_list = []
        for tag in self.cfg:
            for attr in self.cfg[tag]:
                cmd_list.append(self.ret_info(
                    tag, attr, 'class', dprefix, hide)
                )
                cmd_list.append(self.ret_info(
                    tag, attr, 'instance', dprefix, hide)
                )
        self.cmd_list = filter(lambda str: str != '', cmd_list)

    # nsd need this function
    def get_geom(self, tag: str) -> str:
        """ External function used by nsd
        """
        return self.parsed_geom[tag]

    def parse_geom(self, tag: str) -> str:
        """ Convert geometry from self.cfg format to i3 commands.

        Args:
            tag (str): target self.cfg tag
        """
        rd = {'width': 1920, 'height': 1200}  # resolution_default
        cr = self.current_resolution          # current resolution

        g = re.split(r'[x+]', self.cfg[tag]["geom"])
        cg = []  # converted_geom

        cg.append(int(int(g[0])*cr['width'] / rd['width']))
        cg.append(int(int(g[1])*cr['height'] / rd['height']))
        cg.append(int(int(g[2])*cr['width'] / rd['width']))
        cg.append(int(int(g[3])*cr['height'] / rd['height']))

        return "move absolute position {2} {3}, resize set {0} {1}".format(*cg)

