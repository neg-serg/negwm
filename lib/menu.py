""" Menu manager module.

    This module is about creating various menu.

    For now it contains following menus:
        - Goto workspace.
        - Attach to workspace.
        - Add window to named scratchpad or circle group.
        - xprop menu to get X11-atom parameters of selected window.
        - i3-cmd menu with autocompletion.
"""

import importlib
from typing import List

from cfg import cfg
from misc import Misc
from negi3mod import negi3mod


class menu(negi3mod, cfg):
    """ Base class for menu module """

    def __init__(self, i3ipc) -> None:
        # Initialize cfg.
        cfg.__init__(self, i3ipc)

        # i3ipc connection, bypassed by negi3wm runner
        self.i3ipc = i3ipc

        # i3 path used to get "send" binary path
        self.i3_path = Misc.i3path()

        # i3-msg application name
        self.i3cmd = self.conf("i3cmd")

        # Window properties shown by xprop menu.
        self.xprops_list = self.conf("xprops_list")

        # cache screen width
        if not self.conf("use_default_width"):
            from display import Display
            self.screen_width = Display.get_screen_resolution()["width"]
        else:
            self.screen_width = int(self.conf('use_default_width'))

        for mod in self.cfg['modules']:
            module = importlib.import_module('menu_mods.' + mod)
            setattr(self, mod, getattr(module, mod)(self))

        self.bindings = {
            "cmd_menu": self.i3menu.cmd_menu,

            "xprop": self.xprop.xprop,

            "autoprop": self.props.autoprop,
            "show_props": self.props.show_props,

            "pulse_output": self.pulse_menu.pulseaudio_output,
            "pulse_input": self.pulse_menu.pulseaudio_input,

            "ws": self.winact.goto_ws,
            "goto_win": self.winact.goto_win,
            "attach": self.winact.attach_win,
            "movews": self.winact.move_to_ws,

            "gtk_theme": self.gnome.change_gtk_theme,
            "icon_theme": self.gnome.change_icon_theme,

            "xrandr_resolution": self.xrandr.change_resolution_xrandr,

            "reload": self.reload_config,
        }

    def args(self, params: dict) -> List[str]:
        """ Create run parameters to spawn rofi process from dict

            Args:
                params(dict): parameters for rofi
            Return:
                List(str) to do rofi subprocessing
        """
        prompt = self.conf("prompt")

        params['width'] = params.get('width', int(self.screen_width * 0.85))
        params['prompt'] = params.get('prompt', prompt)
        params['cnum'] = params.get('cnum', 16)
        params['lnum'] = params.get('lnum', 2)
        params['markup_rows'] = params.get('markup_rows', '-no-markup-rows')
        params['auto_selection'] = \
            params.get('auto_selection', "-no-auto-selection")

        launcher_font = self.conf("font") + " " + \
            str(self.conf("font_size"))
        location = self.conf("location")
        anchor = self.conf("anchor")
        matching = self.conf("matching")
        gap = self.conf("gap")

        return [
            'rofi', '-show', '-dmenu',
            '-columns', str(params['cnum']),
            '-lines', str(params['lnum']),
            '-disable-history',
            params['auto_selection'],
            params['markup_rows'],
            '-p', params['prompt'],
            '-i',
            '-matching', f'{matching}',
            '-theme-str',
            f'* {{ font: "{launcher_font}"; }}',
            '-theme-str',
            f'#window {{ width:{params["width"]}; y-offset: -{gap}; \
            location: {location}; \
            anchor: {anchor}; }}',
        ]

    def wrap_str(self, string: str) -> str:
        """ String wrapper to make it beautiful """
        return self.conf('left_bracket') + string + self.conf('right_bracket')
