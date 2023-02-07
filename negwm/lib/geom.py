""" Module to convert from 16:10 1080p geometry to target screen geometry.
This module contains geometry converter and also i3-rules generator. Also
in this module geometry is parsed from config X11 internal format to the i3
commands. """

import re
from negwm.lib.display import Display

class geom():
    def __init__(self, cfg: dict) -> None:
        """ Init function
        cfg: config bypassed from target module, nsd for example. """
        self.cmd_list = [] # Generated command list for i3 config
        self.parsed_geom = {} # Geometry in the i3-commands format.
        # Set current screen resolution
        self.current_resolution = Display.get_screen_resolution()
        self.cfg = cfg # External config
        # Fill self.parsed_geom with self.parse_geom function.
        for tag in self.cfg:
            if isinstance(self.cfg[tag], dict):
                self.parsed_geom[tag] = self.parse_geom(tag)

    # Scratchpad need this function
    def get_geom(self, tag: str) -> str:
        """ External function used by nsd """
        return self.parsed_geom[tag]

    def parse_geom(self, tag: str) -> str:
        """ Convert geometry from self.cfg format to i3 commands.
            tag (str): target self.cfg tag """
        rd = {'width': 3840, 'height': 2160} # resolution_default
        cr = self.current_resolution # current resolution
        g = re.split(r'[x+]', self.cfg[tag]["geom"])
        cg = [] # converted_geom
        cg.append(int(int(g[0])*cr['width'] / rd['width']))
        cg.append(int(int(g[1])*cr['height'] / rd['height']))
        cg.append(int(int(g[2])*cr['width'] / rd['width']))
        cg.append(int(int(g[3])*cr['height'] / rd['height']))
        return "move absolute position {2} {3}, resize set {0} {1}".format(*cg)
