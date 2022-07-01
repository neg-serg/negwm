""" Menu manager module. This module is about creating various menu. For now it
contains following menus:
    - Goto workspace.
    - Attach to workspace.
    - Add window to named scratchpad or circle group.
    - xprop menu to get X11-atom parameters of selected window.
    - i3-cmd menu with autocompletion. """

import importlib
from typing import List

from .cfg import cfg
from .misc import Misc
from .extension import extension


class menu(extension, cfg):
    """ Base class for menu module """
    def __init__(self, i3ipc) -> None:
        extension.__init__(self)
        cfg.__init__(self, i3ipc)
        self.i3ipc = i3ipc
        self.i3_path = Misc.negwm_path()
        self.i3cmd = self.conf("i3cmd") # i3-msg application name
        # Window properties shown by xprop menu.
        self.xprops_list = self.conf("xprops_list")
        for mod in self.cfg['modules']:
            module = importlib.import_module('menu_mods.' + mod)
            setattr(self, mod, getattr(module, mod)(self))
        self.cmd_menu = getattr(self, 'i3menu').cmd_menu
        self.xprop_show = getattr(self, 'xprop').xprop
        self.autoprop = getattr(self, 'props').autoprop
        self.show_props = getattr(self, 'props').show_props
        self.pulse_output = getattr(self, 'pulse_menu').pulseaudio_output
        self.pulse_input = getattr(self, 'pulse_menu').pulseaudio_input
        self.pulse_mute = getattr(self, 'pulse_menu').pulseaudio_mute
        self.ws = getattr(self, 'winact').goto_ws
        self.goto_win = getattr(self, 'winact').goto_win
        self.attach = getattr(self, 'winact').attach_win
        self.movews = getattr(self, 'winact').move_to_ws
        self.gtk_theme = getattr(self, 'gnome').change_gtk_theme
        self.icon_theme = getattr(self, 'gnome').change_icon_theme
        self.xrandr_resolution = getattr(self, 'xrandr').change_resolution_xrandr
        self.reload = self.reload

    def args(self, params: dict) -> List[str]:
        """ Create run parameters to spawn rofi process from dict
            params(dict): parameters for rofi
            List(str) to do rofi subprocessing """
        prompt = self.conf("prompt")
        params['prompt'] = params.get('prompt', prompt)
        params['cnum'] = params.get('cnum', 16)
        params['lnum'] = params.get('lnum', 2)
        params['markup_rows'] = params.get('markup_rows', '-no-markup-rows')
        params['auto_selection'] = \
            params.get('auto_selection', "-no-auto-selection")
        matching = self.conf("matching")
        return [
            'rofi', '-show', '-dmenu',
            '-columns', str(params['cnum']),
            '-lines', str(params['lnum']),
            '-disable-history',
            params['auto_selection'], params['markup_rows'],
            '-p', params['prompt'], '-i',
            '-matching', f'{matching}']

    def wrap_str(self, string: str) -> str:
        """ String wrapper to make it beautiful """
        return self.conf('left_bracket') + string + self.conf('right_bracket')
