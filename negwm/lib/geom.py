""" Module to convert some screen geometry to target screen geometry. This module contains geometry converter and also i3-rules generator.
"""

import re
from negwm.lib.display import Display

class Geom():
    resolution_default = {'width': 3440, 'height': 1440}
    
    def __init__(self, cfg: dict={}, geom_in_json='') -> None:
        """ Init function
        cfg: config bypassed from target module, nsd for example. """
        self.move_cmds = {} # Command to move windows to the desired geometry.
        self.parsed_geom = {} # Geometry after parse
        self.converted_geom = {} # Geometry in the list format for future reuse after conversion
        self.current_resolution = Display.get_screen_resolution()
        if cfg:
            self.cfg = cfg # External config
            for tag in self.cfg:
                if isinstance(self.cfg[tag], dict):
                    self.parse_geom(tag)
                    self.converted_geom[tag] = self.convert_geom()
                    self.move_cmds[tag] = self.window_move_cmd(self.converted_geom[tag])
        elif geom_in_json:
            pass
        else:
            pass # fatal

    def get_geom_by_tag(self, tag: str) -> str:
        """ External function used by nsd """
        return self.move_cmds[tag]

    def convert_geom(self, external_geom={}) -> list:
        """ Convert geom to desired size """
        cr = self.current_resolution # current resolution
        rd = Geom.resolution_default
        ret = [] # converted_geom
        geom_to_convert=self.parsed_geom
        if external_geom:
            geom_to_convert=external_geom
        ret.append(int(int(geom_to_convert[0]) * cr['width'] / rd['width']))
        ret.append(int(int(geom_to_convert[1]) * cr['height'] / rd['height']))
        ret.append(int(int(geom_to_convert[2]) * cr['width'] / rd['width']))
        ret.append(int(int(geom_to_convert[3]) * cr['height'] / rd['height']))
        return ret

    def parse_geom(self, tag: str='', geom_list: list=[]) -> None:
        """ Parse geometry from self.cfg format to the list of ints
            tag (str): target self.cfg tag """
        if tag:
            geom_list = re.split(r'[x+]', self.cfg[tag]["geom"])
        if not geom_list:
            pass # fatal
        for num, side in enumerate(geom_list):
            geom_list[num] = float(side)
        self.parsed_geom = geom_list
        
    def window_move_cmd(self, geom: list):
        return f"move absolute position {geom[2]} {geom[3]}, resize set {geom[0]} {geom[1]}"
