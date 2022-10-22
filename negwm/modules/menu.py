""" Menu manager module. This module is about creating various menu. For now it
contains following menus:
    - Add window to named scratchpad or circle group.
    - Attach to workspace.
    - Goto workspace.
    - i3-cmd menu with autocompletion.
    - xprop menu to get X11-atom parameters of selected window. """

import importlib
from typing import List

from negwm.lib.cfg import cfg
from negwm.lib.extension import extension


class menu(extension, cfg):
    """ Base class for menu module """
    def __init__(self, i3ipc) -> None:
        extension.__init__(self)
        cfg.__init__(self, i3ipc)
        self.i3ipc = i3ipc
        self.i3cmd = self.conf('i3cmd') # i3-msg application name
        # Window properties shown by xprop menu.
        self.xprops_list = self.conf('xprops_list')
        for mod in self.cfg['modules']:
            module = importlib.import_module('negwm.modules.menu_mods.' + mod)
            setattr(self, mod, getattr(module, mod)(self))
        self.i3_menu = getattr(self, 'i3menu').i3_menu
        self.xprop_show = getattr(self, 'xprop').xprop
        self.move_window = getattr(self, 'props').move_window
        self.show_props = getattr(self, 'props').show_props
        self.pulse_output = getattr(self, 'pulse_menu').pulseaudio_output
        self.pulse_input = getattr(self, 'pulse_menu').pulseaudio_input
        self.pulse_mute = getattr(self, 'pulse_menu').pulseaudio_mute
        self.ws = getattr(self, 'winact').goto_ws
        self.goto_win = getattr(self, 'winact').goto_win
        self.attach = getattr(self, 'winact').attach_win
        self.movews = getattr(self, 'winact').move_to_ws
        self.xrandr_resolution = getattr(self, 'xrandr').change_resolution_xrandr
        self.reload = self.reload

    def args(self, params: dict) -> List[str]:
        """ Create run parameters to spawn rofi process from dict
            params(dict): parameters for rofi
            List(str) to do rofi subprocessing """
        prompt = self.conf("prompt")
        params['prompt'] = params.get('prompt', prompt)
        params['markup_rows'] = params.get('markup_rows', '-no-markup-rows')
        params['auto-select'] = \
            params.get('auto-select', "-no-auto-select")
        matching = self.conf("matching")
        return [
            'rofi', '-show', '-dmenu', '-disable-history',
            params['auto-select'], params['markup_rows'],
            '-p', params['prompt'], '-i', '-matching', f'{matching}']

    def wrap_str(self, string: str) -> str:
        """ String wrapper to make it beautiful """
        return self.conf('left_bracket') + string + self.conf('right_bracket')
