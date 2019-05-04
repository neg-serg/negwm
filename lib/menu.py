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

    def rofi_args(self, prompt: str = '>', cnum: int = 16,
                  lnum: int = 2,
                  width: int = 0,
                  markup_rows: str = '',
                  auto_selection="-no-auto-selection") -> List[str]:
        prompt = prompt or self.prompt
        width = width or int(self.screen_width * 0.85)
        markup_rows = markup_rows or '-no-markup-rows'

        """ Returns arguments list for rofi runner.

        Args:
            prompt (str): rofi prompt, optional.
            cnum (int): number of columns, optional.
            lnum (int): number of lines, optional.
            width (int): width of rofi menu, optional.
            markup_rows (str): markup rows setting.
        """
        return [
            'rofi', '-show', '-dmenu',
            '-columns', str(cnum), '-lines', str(lnum),
            '-disable-history',
            auto_selection,
            markup_rows,
            '-p', prompt,
            '-i',  # non case-sensitive
            '-matching', f'{self.matching}',
            '-theme-str', f'* {{ font: "{self.launcher_font}"; }}',
            '-theme-str', f'#window {{ width:{width}; y-offset: -{self.gap}; \
            location: {self.location}; \
            anchor: {self.anchor}; }}',
        ]

    def wrap_str(self, s: str) -> str:
        return self.lhs_br + s + self.rhs_br

