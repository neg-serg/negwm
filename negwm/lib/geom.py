""" Module to convert some screen geometry to target screen geometry. This module contains geometry converter and also i3-rules generator.
"""

import re
from negwm.lib.display import Display

class Geom():
    resolution_default = {'width': 3440, 'height': 1440}
    
    def __init__(self, cfg: dict) -> None:
        """ Init function
        cfg: config bypassed from target module, nsd for example. """
        self.geom = {} # Command to move windows to the desired geometry.
        self.parsed_geom = {} # Geometry after parse
        self.converted_geom = {} # Geometry in the list format for future reuse after conversion
        self.current_resolution = Display.get_screen_resolution()
        self.cfg = cfg # External config
        for tag in self.cfg:
            if isinstance(self.cfg[tag], dict):
                self.converted_geom[tag] = self.convert_geom(self.parse_geom(tag))
                self.geom[tag] = self.window_move_cmd(self.converted_geom[tag])

    # Scratchpad need this function
    def get_geom(self, tag: str) -> str:
        """ External function used by nsd """
        return self.geom[tag]

    def convert_geom(self, geom) -> list:
        """ Convert geom to desired size """
        cr = self.current_resolution # current resolution
        rd = Geom.resolution_default
        ret = [] # converted_geom
        ret.append(int(int(geom[0])*cr['width'] / rd['width']))
        ret.append(int(int(geom[1])*cr['height'] / rd['height']))
        ret.append(int(int(geom[2])*cr['width'] / rd['width']))
        ret.append(int(int(geom[3])*cr['height'] / rd['height']))
        return ret

    def parse_geom(self, tag: str) -> list:
        """ Parse geometry from self.cfg format to the list of ints
            tag (str): target self.cfg tag """
        g = re.split(r'[x+]', self.cfg[tag]["geom"])
        for num, side in enumerate(g):
            g[num] = float(side)
        return g
        
    def window_move_cmd(self, geom: list):
        return f"move absolute position {geom[2]} {geom[3]}, resize set {geom[0]} {geom[1]}"
