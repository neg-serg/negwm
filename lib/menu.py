""" Menu manager module.

    This module is about creating various menu.

    For now it contains following menus:
        - Goto workspace.
        - Attach to workspace.
        - Add window to named scratchpad or circle group.
        - xprop menu to get X11-atom parameters of selected window.
        - i3-cmd menu with autocompletion.
"""

from singleton import Singleton
from cfg import cfg
from misc import Misc
from display import Display
from typing import List
import importlib


class menu(cfg):
    __metaclass__ = Singleton

    def __init__(self, i3, loop=None) -> None:
        # Initialize cfg.
        cfg.__init__(self, i3)

        # i3ipc connection, bypassed by negi3mods runner
        self.i3 = i3

        # i3 path used to get "send" binary path
        self.i3_path = Misc.i3path()

        # i3-msg application name
        self.i3cmd = self.conf("i3cmd")

        # Window properties shown by xprop menu.
        self.xprops_list = self.conf("xprops_list")

        # cache screen width
        self.screen_width = Display.get_screen_resolution()["width"]

        # set up settings for rofi, dmenu, whatever
        self.launcher_font = self.conf("font") + " " + \
            str(self.conf("font_size"))
        self.location = self.conf("location")
        self.anchor = self.conf("anchor")
        self.matching = self.conf("matching")
        self.prompt = self.conf("prompt")
        self.lhs_br = self.conf('left_bracket')
        self.rhs_br = self.conf('right_bracket')

        self.gap = self.conf('gap')

        for mod in self.cfg['modules']:
            module = importlib.import_module('menu_mods.' + mod)
            setattr(self, mod, getattr(module, mod)(self))

    def switch(self, args: List) -> None:
        """ Defines pipe-based IPC for nsd module. With appropriate function
            bindings.

            This function defines bindings to the named_scratchpad methods that
            can be used by external users as i3-bindings, sxhkd, etc. Need the
            [send] binary which can send commands to the appropriate FIFO.

            Args:
                args (List): argument list for the selected function.
        """
        {
            "cmd_menu": self.i3menu.cmd_menu,

            "xprop": self.xprop.xprop_menu,

            "autoprop": self.props.autoprop,
            "show_props": self.props.show_props,

            "pulse_output": self.pulse_menu.pulseaudio_output,
            "pulse_input": self.pulse_menu.pulseaudio_input,

            "ws": self.winact.goto_ws,
            "goto_win": self.winact.goto_win,
            "attach": self.winact.attach_win,
            "movews": self.winact.move_to_ws,

            "gtk_theme": self.gtk.change_gtk_theme,
            "xrandr_resolution": self.xrandr.change_resolution_xrandr,

            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def rofi_args(self, params: dict()) -> List[str]:
        params['width'] = params.get('width', 0) or \
            int(self.screen_width * 0.85)
        params['prompt'] = params.get('prompt', 0) or self.prompt
        params['cnum'] = params.get('cnum', 0) or 16
        params['lnum'] = params.get('lnum', 0) or 2
        params['markup_rows'] = params.get('markup_rows', 0) or \
            '-no-markup-rows'
        params['auto_selection'] = params.get('auto_selection', 0) or \
            "-no-auto-selection"

        """ Returns arguments list for rofi runner.

        Args:
            params(dict): dict for rofi parameters.
        """
        return [
            'rofi', '-show', '-dmenu',
            '-columns', str(params['cnum']),
            '-lines', str(params['lnum']),
            '-disable-history',
            params['auto_selection'],
            params['markup_rows'],
            '-p', params['prompt'],
            '-i',  # non case-sensitive
            '-matching', f'{self.matching}',
            '-theme-str', f'* {{ font: "{self.launcher_font}"; }}',
            '-theme-str', f'#window {{ width:{params["width"]}; y-offset: -{self.gap}; \
            location: {self.location}; \
            anchor: {self.anchor}; }}',
        ]

    def wrap_str(self, s: str) -> str:
        return self.lhs_br + s + self.rhs_br

