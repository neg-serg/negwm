""" 2bwm-like features module.

There are a lot of various actions over the floating windows in this module,
which may reminds you 2bwm, subtle, or another similar window managers.

You can change window geometry, move it to the half or quad size of the screen
space, etc.

"""

import collections
from itertools import cycle
from typing import List, Mapping, Iterator
from main import find_visible_windows
from main import Negi3ModsDisplay
from singleton import Singleton
from modi3cfg import modi3cfg


class wm3(Singleton, modi3cfg):
    def __init__(self, i3, loop=None) -> None:
        """ Init function

        Main part is in self.initialize, which performs initialization itself.

        Attributes:
            i3: i3ipc connection
            loop: asyncio loop. It's need to be given as parameter because of
                  you need to bypass asyncio-loop to the thread
        """
        # Initialize modi3cfg.
        modi3cfg.__init__(self, i3)
        self.initialize(i3)

    def initialize(self, i3) -> None:
        # i3ipc connection, bypassed by negi3mods runner.
        self.i3 = i3

        # cache list length
        maxlength = self.conf("cache_list_size")

        # create list with the finite number of elements by the [None] * N hack
        self.geom_list = collections.deque(
            [None] * maxlength,
            maxlen=maxlength
        )

        # we need to know current resolution for almost all operations here.
        self.current_resolution = Negi3ModsDisplay.get_screen_resolution()

        # here we load information about useless gaps
        self.load_useless_gaps()

        # config about useless gaps for quad splitting, True by default
        self.quad_use_gaps = self.conf("quad_use_gaps")

        # config about useless gaps for half splitting, True by default
        self.x2_use_gaps = self.conf("x2_use_gaps")

        # coeff to grow window in all dimensions
        self.grow_coeff = self.conf("grow_coeff")

        # coeff to shrink window in all dimensions
        self.shrink_coeff = self.conf("shrink_coeff")

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
            "reload": self.reload_config,
            "focus_next_visible": self.focus_next,
            "focus_prev_visible": self.focus_next(reversed_order=True),
            "maximize": self.maximize,
            "maxhor": lambda: self.maximize(by='X'),
            "maxvert": lambda: self.maximize(by='Y'),
            "x2": self.x2,
            "x4": self.quad,
            "quad": self.quad,
            "grow": self.grow,
            "shrink": self.shrink,
            "center": self.move_center,
            "revert_maximize": self.revert_maximize,
        }[args[0]](*args[1:])

    def load_useless_gaps(self) -> None:
        """ Load useless gaps settings.
        """
        try:
            self.useless_gaps = self.cfg.get("useless_gaps", {
                    "w": 12, "a": 12, "s": 12, "d": 12
                }
            )
            for field in ["w", "a", "s", "d"]:
                if self.useless_gaps[field] < 0:
                    self.useless_gaps[field] = abs(self.useless_gaps[field])
        except (KeyError, TypeError, AttributeError):
            self.useless_gaps = {"w": 0, "a": 0, "s": 0, "d": 0}

    def center_geom(self, win,
                    change_geom: bool = False, degrade_coeff: float = 0.82):
        """ Move window to the center with geometry optional changing.

        Args:
            win: target window.
            change_geom (bool): predicate to change geom to the [degrade_coeff]
                                of the screen space in both dimenhions.
            degrade_coeff (int): coefficient which denotes change geom of the
                                 target window.
        """
        geom = {}
        center = {}

        if degrade_coeff > 1.0:
            degrade_coeff = 1.0

        center['x'] = int(self.current_resolution['width'] / 2)
        center['y'] = int(self.current_resolution['height'] / 2)

        if not change_geom:
            geom['width'] = int(win.rect.width)
            geom['height'] = int(win.rect.height)
        else:
            geom['width'] = int(
                self.current_resolution['width'] * degrade_coeff
            )
            geom['height'] = int(
                self.current_resolution['height'] * degrade_coeff
            )

        geom['x'] = center['x'] - int(geom['width'] / 2)
        geom['y'] = center['y'] - int(geom['height'] / 2)

        return geom

    def move_center(self, resize: str) -> None:
        """ Move window to center.

        Args:
            resize (str): predicate which shows resize target window or not.

        """
        focused = self.i3.get_tree().find_focused()
        if "default" == resize or "none" == resize:
            geom = self.center_geom(focused)
            self.set_geom(focused, geom)
        elif "resize" == resize or "on" == resize or "yes" == resize:
            geom = self.center_geom(focused, change_geom=True)
            self.set_geom(focused, geom)
        else:
            return

    def get_prev_geom(self):
        """ Get previous window geometry.
        """
        self.geom_list.append(
            {
                "id": self.current_win.id,
                "geom": self.save_geom()
            }
        )
        return self.geom_list[-1]["geom"]

    def multiple_geom(self, win, coeff: float) -> Mapping[str, int]:
        """ Generic function to shrink/grow floating window geometry.

            Args:
                win: target window.
                coeff (float): generic coefficient which denotes grow/shrink
                               geom of the target window.
        """
        return {
            'x': int(win.rect.x),
            'y': int(win.rect.y),
            'width': int(win.rect.width * coeff),
            'height': int(win.rect.height * coeff),
        }

    def grow(self) -> None:
        """ Grow floating window geometry by [self.grow_coeff].
        """
        focused = self.i3.get_tree().find_focused()
        geom = self.multiple_geom(focused, self.grow_coeff)
        self.set_geom(focused, geom)

    def shrink(self) -> None:
        """ Shrink floating window geometry by [self.shrink_coeff].
        """
        focused = self.i3.get_tree().find_focused()
        geom = self.multiple_geom(focused, self.shrink_coeff)
        self.set_geom(focused, geom)

    def x2(self, mode: str) -> None:
        """ Move window to the 1st or 2nd half of the screen space with the
            given orientation.

        Args:
            mode (h1,h2,v1,v2): defines h1,h2,v1 or v2 half of
                                screen space to move.
        """
        curr_scr = self.current_resolution
        self.current_win = self.i3.get_tree().find_focused()

        if self.x2_use_gaps:
            gaps = self.useless_gaps
        else:
            gaps = {"w": 0, "a": 0, "s": 0, "d": 0}

        half_width = int(curr_scr['width'] / 2)
        half_height = int(curr_scr['height'] / 2)
        double_dgaps = int(gaps['d'] * 2)
        double_sgaps = int(gaps['s'] * 2)

        if 'h1' == mode or 'hup' == mode:
            geom = {
                'x': gaps['a'],
                'y': gaps['w'],
                'width': curr_scr['width'] - double_dgaps,
                'height': half_height - double_sgaps,
            }
        elif 'h2' == mode or 'hdown' == mode:
            geom = {
                'x': gaps['a'],
                'y': half_height + gaps['w'],
                'width': curr_scr['width'] - double_dgaps,
                'height': half_height - double_sgaps,
            }
        elif 'v1' == mode or 'vleft' == mode:
            geom = {
                'x': gaps['a'],
                'y': gaps['w'],
                'width': half_width - double_dgaps,
                'height': curr_scr['height'] - double_sgaps,
            }
        elif 'v2' == mode or 'vright' == mode:
            geom = {
                'x': gaps['a'] + half_width,
                'y': gaps['w'],
                'width': half_width - double_dgaps,
                'height': curr_scr['height'] - double_sgaps,
            }
        else:
            return

        if self.current_win is not None:
            if not self.geom_list[-1]:
                self.get_prev_geom()
            elif self.geom_list[-1]:
                prev = self.geom_list[-1].get('id', {})
                if prev != self.current_win.id:
                    geom = self.get_prev_geom()

            self.set_geom(self.current_win, geom)

    def quad(self, mode: int) -> None:
        """ Move window to the 1,2,3,4 quad of 2D screen space

        Args:
            mode (1,2,3,4): defines 1,2,3 or 4 quad of
                            screen space to move.
        """
        try:
            mode = int(mode)
        except TypeError:
            print("cannot convert mode={mode} to int")
            return

        curr_scr = self.current_resolution
        self.current_win = self.i3.get_tree().find_focused()

        if self.quad_use_gaps:
            gaps = self.useless_gaps
        else:
            gaps = {"w": 0, "a": 0, "s": 0, "d": 0}

        half_width = int(curr_scr['width'] / 2)
        half_height = int(curr_scr['height'] / 2)
        double_dgaps = int(gaps['d'] * 2)
        double_sgaps = int(gaps['s'] * 2)

        if 1 == mode:
            geom = {
                'x': gaps['a'],
                'y': gaps['w'],
                'width': half_width - double_dgaps,
                'height': half_height - double_sgaps,
            }
        elif 2 == mode:
            geom = {
                'x': half_width + gaps['a'],
                'y': gaps['w'],
                'width': half_width - double_dgaps,
                'height': half_height - double_sgaps,
            }
        elif 3 == mode:
            geom = {
                'x': gaps['a'],
                'y': gaps['w'] + half_height,
                'width': half_width - double_dgaps,
                'height': half_height - double_sgaps,
            }
        elif 4 == mode:
            geom = {
                'x': gaps['a'] + half_width,
                'y': gaps['w'] + half_height,
                'width': half_width - double_dgaps,
                'height': half_height - double_sgaps,
            }
        else:
            return

        if self.current_win is not None:
            if not self.geom_list[-1]:
                self.get_prev_geom()
            elif self.geom_list[-1]:
                prev = self.geom_list[-1].get('id', {})
                if prev != self.current_win.id:
                    geom = self.get_prev_geom()

            self.set_geom(self.current_win, geom)

    def maximize(self, by: str = 'XY') -> None:
        """ Maximize window by attribute.

        Args:
            by (str): maximize by X, Y or XY.
        """
        geom = {}

        self.current_win = self.i3.get_tree().find_focused()
        if self.current_win is not None:
            if not self.geom_list[-1]:
                geom = self.get_prev_geom()
            elif self.geom_list[-1]:
                prev = self.geom_list[-1].get('id', {})
                if prev != self.current_win.id:
                    geom = self.get_prev_geom()
                else:
                    # do nothing
                    return
            if 'XY' == by or 'YX' == by:
                max_geom = self.maximized_geom(
                    geom.copy(), byX=True, byY=True
                )
            elif 'X' == by:
                max_geom = self.maximized_geom(
                    geom.copy(), byX=True, byY=False
                )
            elif 'Y' == by:
                max_geom = self.maximized_geom(
                    geom.copy(), byX=False, byY=True
                )
            self.set_geom(self.current_win, max_geom)

    def revert_maximize(self) -> None:
        """ Revert changed window state.
        """
        try:
            focused = self.i3.get_tree().find_focused()
            if self.geom_list[-1].get("geom", {}):
                self.set_geom(focused, self.geom_list[-1]["geom"])
            del self.geom_list[-1]
        except (KeyError, TypeError, AttributeError):
            pass

    def maximized_geom(self, geom: dict, gaps: dict = {},
                       byX: bool = False, byY: bool = False) -> dict:
        """ Return maximized geom.

        Args:
            geom (dict): var to return maximized geometry.
            gaps (dict): dict to define useless gaps.
            byX (bool): maximize by X.
            byY (bool): maximize by Y.
        """
        if gaps == {}:
            gaps = self.useless_gaps
        if byX:
            geom['x'] = 0 + gaps['a']
            geom['width'] = self.current_resolution['width'] - gaps['d'] * 2
        if byY:
            geom['y'] = 0 + gaps['w']
            geom['height'] = self.current_resolution['height'] - gaps['s'] * 2
        return geom

    def set_geom(self, win, geom: dict) -> dict:
        """ Generic function to set geometry.

        Args:
            win: target window to change windows.
            geom (dict): geometry.
        """
        win.command(f"move absolute position {geom['x']} {geom['y']}")
        win.command(f"resize set {geom['width']} {geom['height']} px")

    def create_geom_from_rect(self, rect) -> dict:
        """ Create geometry from the given rectangle.

        Args:
            rect: rect to extract geometry from.

        """
        geom = {}
        geom['x'] = rect.x
        geom['y'] = rect.y
        geom['height'] = rect.height
        geom['width'] = rect.width

        return geom

    def save_geom(self, target_win=None) -> dict:
        """ Save geometry.

        Args:
            target_win: [optional] denotes target window.

        """
        if target_win is None:
            target_win = self.current_win
        return self.create_geom_from_rect(target_win.rect)

    def get_windows_on_ws(self) -> Iterator:
        """ Get windows on the current workspace.
        """
        return filter(
            lambda x: x.window,
            self.i3.get_tree().find_focused().workspace().descendents()
        )

    def focus_next(self, reversed_order: bool = False) -> None:
        """ Focus next visible window.

        Args:
            reversed_order(bool) : [optional] predicate to change order.

        """
        visible_windows = find_visible_windows(self.get_windows_on_ws())
        if reversed_order:
            cycle_windows = cycle(reversed(visible_windows))
        else:
            cycle_windows = cycle(visible_windows)
        for window in cycle_windows:
            if window.focused:
                focus_to = next(cycle_windows)
                self.i3.command('[id="%d"] focus' % focus_to.window)
                break

