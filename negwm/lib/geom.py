""" Module to convert some screen geometry to target screen geometry. This module contains geometry converter and also i3-rules generator.
"""

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
        cr = self.current_resolution # current resolution
        g = re.split(r'[x+]', self.cfg[tag]["geom"])
        for num, side in enumerate(g):
            g[num] = float(side)
        cg = [] # converted_geom
        cg_ppt = []

        cg.append(int(g[0]))
        cg.append(int(g[1]))
        cg.append(int(g[2]))
        cg.append(int(g[3]))
        
        cg_ppt.append(round(g[0]/float(cr['width'])*100.0))
        cg_ppt.append(round(g[1]/float(cr['height'])*100.0))
        cg_ppt.append(round(g[2]/float(cr['width'])*100.0))
        cg_ppt.append(round(g[3]/float(cr['height'])*100.0))

        return "move absolute position {2} {3}, resize set {0} {1}".format(*cg)
