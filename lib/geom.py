""" Module to convert from 16:10 1080p geometry to target screen geometry.

    This module contains geometry converter and also i3-rules generator. Also
    in this module geometry is parsed from config X11 internal format to the i3
    commands.
"""

import re
from typing import List
from display import Display
from misc import Misc


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
        self.current_resolution = Display.get_screen_resolution()

        # external config
        self.cfg = cfg

        # fill self.parsed_geom with self.parse_geom function.
        for tag in self.cfg:
            self.parsed_geom[tag] = self.parse_geom(tag)

    @staticmethod
    def scratchpad_hide_cmd(hide: bool) -> str:
        """ Returns cmd needed to hide scratchpad.

            Args:
                hide (bool): to hide target or not.
        """
        ret = ""
        if hide:
            ret = ", [con_id=__focused__] scratchpad show"
        return ret

    def bscratch_info(self, tag: str, attr: str, target_attr: str,
                 dprefix: str, hide: bool) -> str:
        """ Create rule in i3 commands format

        Args:
            tag (str): target tag.
            attr (str): tag attrubutes.
            target_attr (str): attribute to fill.
            dprefix (str): rule prefix.
            hide (bool): to hide target or not.
        """
        if target_attr in attr:
            lst = [item for item in self.cfg[tag][target_attr] if item != '']
            if lst != []:
                pref = dprefix+"[" + '{}="'.format(attr) + \
                    Misc.ch(self.cfg[tag][attr], '^')
                for_win_cmd = pref + Misc.parse_attr(self.cfg[tag][attr]) + \
                    "move scratchpad, " + self.get_geom(tag) \
                        + self.scratchpad_hide_cmd(hide)
                return for_win_cmd
        return ''

    def i3match_gen(self,
                    hide: bool = False,
                    dprefix: str = "for_window "
                    ) -> List:
        """ Create i3 match rules for all tags.

        Args:
            hide (bool): to hide target or not, optional.
            dprefix (str): i3-cmd prefix is "for_window " by default, optional.
        """
        cmd_list = []
        for tag in self.cfg:
            for attr in self.cfg[tag]:
                if attr in {"class_r", "instance_r", "name_r", "role_r"}:
                    attr = attr[:-2]
                cmd_list.append(self.bscratch_info(
                    tag, attr, 'class', dprefix, hide)
                )
                cmd_list.append(self.bscratch_info(
                    tag, attr, 'instance', dprefix, hide)
                )
                cmd_list.append(self.bscratch_info(
                    tag, attr, 'name', dprefix, hide)
                )
        self.cmd_list = filter(lambda str: str != '', cmd_list)
        return list(self.cmd_list)

    # nsd need this function
    def get_geom(self, tag: str) -> str:
        """ External function used by nsd """
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
