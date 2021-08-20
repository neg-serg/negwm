""" 2bwm-like features module.
There are a lot of various actions over the floating windows in this module,
which may reminds you 2bwm, subtle, or another similar window managers. You can
change window geometry, move it to the half or quad size of the screen space,
etc. Partially code is taken from https://github.com/miseran/i3-tools, thanks
to you, miseran(https://github.com/miseran)
"""

import collections
import sys
from typing import Mapping

from . display import Display
from . cfg import cfg
from . extension import extension


class actions(extension, cfg):
    def __init__(self, i3) -> None:
        """ Main part is in self.initialize,
        which performs initialization itself.
        i3: i3ipc connection """
        # Initialize cfg.
        cfg.__init__(self, i3)
        # i3ipc connection, bypassed by negi3wm runner.
        self.i3ipc = i3
        self.i3ipc.on("window::focus", self.auto_tiling)
        maxlength = self.conf("cache_list_size") # cache list length
        # create list with the finite number of elements by the [None] * N hack
        self.geom_list = collections.deque([None] * maxlength, maxlen=maxlength)
        self.current_win = None
        # We need to know current resolution for almost all operations here.
        self.current_resolution = Display.get_screen_resolution()
        # Here we load information about useless gaps
        self.load_useless_gaps()
        # Config about useless gaps for quad splitting, True by default
        self.quad_use_gaps = self.conf("quad_use_gaps")
        # Config about useless gaps for half splitting, True by default
        self.x2_use_gaps = self.conf("x2_use_gaps")
        # Coeff to grow window in all dimensions
        self.grow_coeff = self.conf("grow_coeff")
        # Coeff to shrink window in all dimensions
        self.shrink_coeff = self.conf("shrink_coeff")
        self.bindings = {
            "reload": self.reload_config,
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
            "resize": self.resize,
            "tab-focus": self.focus_tab,
            "tab-move": self.move_tab,
            "next_ws": self.next_ws,
        }

    def load_useless_gaps(self) -> None:
        """ Load useless gaps settings. """
        try:
            self.useless_gaps = self.cfg.get("useless_gaps", {
                "w": 12, "a": 12, "s": 12, "d": 12
            })
            for field in ["w", "a", "s", "d"]:
                if self.useless_gaps[field] < 0:
                    self.useless_gaps[field] = abs(self.useless_gaps[field])
        except (KeyError, TypeError, AttributeError):
            self.useless_gaps = {"w": 0, "a": 0, "s": 0, "d": 0}

    def center_geom(self, win,
                    change_geom: bool = False, degrade_coeff: float = 0.82):
        """ Move window to the center with geometry optional changing.
        win: target window.
        change_geom (bool): predicate to change geom to the [degrade_coeff]
        of the screen space in both dimenhions.
        degrade_coeff (int): coefficient which denotes change geom of the
        target window. """
        geom, center = {}, {}
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
        """ Move window to center
        resize (str): predicate which shows resize target window or not. """
        focused = self.i3ipc.get_tree().find_focused()
        if resize in {"default", "none"}:
            geom = self.center_geom(focused)
            actions.set_geom(focused, geom)
        elif resize in {"resize", "on", "yes"}:
            geom = self.center_geom(focused, change_geom=True)
            actions.set_geom(focused, geom)
        else:
            return

    def get_prev_geom(self):
        """ Get previous window geometry. """
        self.geom_list.append(
            {
                "id": self.current_win.id,
                "geom": self.save_geom()
            }
        )
        return self.geom_list[-1]["geom"]

    @staticmethod
    def multiple_geom(win, coeff: float) -> Mapping[str, int]:
        """ Generic function to shrink/grow floating window geometry.
                win: target window
                coeff (float): generic coefficient which
                denotes grow/shrink geom of the target window.
        """
        return {
            'x': int(win.rect.x),
            'y': int(win.rect.y),
            'width': int(win.rect.width * coeff),
            'height': int(win.rect.height * coeff),
        }

    def grow(self) -> None:
        """ Grow floating window geometry by [self.grow_coeff]. """
        focused = self.i3ipc.get_tree().find_focused()
        geom = actions.multiple_geom(focused, self.grow_coeff)
        actions.set_geom(focused, geom)

    def shrink(self) -> None:
        """ Shrink floating window geometry by [self.shrink_coeff]. """
        focused = self.i3ipc.get_tree().find_focused()
        geom = actions.multiple_geom(focused, self.shrink_coeff)
        actions.set_geom(focused, geom)

    def x2(self, mode: str) -> None:
        """ Move window to the 1st or 2nd half of the screen space with the
            given orientation.
            mode (h1,h2,v1,v2): defines h1,h2,v1 or v2 half of
                                screen space to move.
        """
        curr_scr = self.current_resolution
        half_width = int(curr_scr['width'] / 2)
        half_height = int(curr_scr['height'] / 2)
        self.current_win = self.i3ipc.get_tree().find_focused()
        if self.x2_use_gaps:
            gaps = self.useless_gaps
        else:
            gaps = {"w": 0, "a": 0, "s": 0, "d": 0}
        double_dgaps = int(gaps['d'] * 2)
        double_sgaps = int(gaps['s'] * 2)
        if mode in {'h1', 'hup'}:
            geom = {
                'x': gaps['a'],
                'y': gaps['w'],
                'width': curr_scr['width'] - double_dgaps,
                'height': half_height - double_sgaps,
            }
        elif mode in {'h2', 'hdown'}:
            geom = {
                'x': gaps['a'],
                'y': half_height + gaps['w'],
                'width': curr_scr['width'] - double_dgaps,
                'height': half_height - double_sgaps,
            }
        elif mode in {'v1', 'vleft'}:
            geom = {
                'x': gaps['a'],
                'y': gaps['w'],
                'width': half_width - double_dgaps,
                'height': curr_scr['height'] - double_sgaps,
            }
        elif mode in {'v2', 'vright'}:
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
            actions.set_geom(self.current_win, geom)

    def quad(self, mode: int) -> None:
        """ Move window to the 1,2,3,4 quad of 2D screen space
            mode (1,2,3,4): defines 1,2,3 or 4 quad of
                            screen space to move.
        """
        try:
            mode = int(mode)
        except TypeError:
            print("cannot convert mode={mode} to int")
            return
        curr_scr = self.current_resolution
        self.current_win = self.i3ipc.get_tree().find_focused()
        if self.quad_use_gaps:
            gaps = self.useless_gaps
        else:
            gaps = {"w": 0, "a": 0, "s": 0, "d": 0}
        half_width = int(curr_scr['width'] / 2)
        half_height = int(curr_scr['height'] / 2)
        double_dgaps = int(gaps['d'] * 2)
        double_sgaps = int(gaps['s'] * 2)
        if mode == 1:
            geom = {
                'x': gaps['a'],
                'y': gaps['w'],
                'width': half_width - double_dgaps,
                'height': half_height - double_sgaps,
            }
        elif mode == 2:
            geom = {
                'x': half_width + gaps['a'],
                'y': gaps['w'],
                'width': half_width - double_dgaps,
                'height': half_height - double_sgaps,
            }
        elif mode == 3:
            geom = {
                'x': gaps['a'],
                'y': gaps['w'] + half_height,
                'width': half_width - double_dgaps,
                'height': half_height - double_sgaps,
            }
        elif mode == 4:
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

            actions.set_geom(self.current_win, geom)

    def maximize(self, by: str = 'XY') -> None:
        """ Maximize window by attribute.
        by (str): maximize by X, Y or XY. """
        geom = {}

        self.current_win = self.i3ipc.get_tree().find_focused()
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
            if by in {'XY', 'YX'}:
                max_geom = self.maximized_geom(
                    geom.copy(), gaps={}, byX=True, byY=True
                )
            elif by == 'X':
                max_geom = self.maximized_geom(
                    geom.copy(), gaps={}, byX=True, byY=False
                )
            elif by == 'Y':
                max_geom = self.maximized_geom(
                    geom.copy(), gaps={}, byX=False, byY=True
                )
            actions.set_geom(self.current_win, max_geom)

    def revert_maximize(self) -> None:
        """ Revert changed window state. """
        try:
            focused = self.i3ipc.get_tree().find_focused()
            if self.geom_list[-1].get("geom", {}):
                actions.set_geom(focused, self.geom_list[-1]["geom"])
            del self.geom_list[-1]
        except (KeyError, TypeError, AttributeError):
            pass

    def maximized_geom(self, geom: dict, gaps: dict,
                       byX: bool = False, byY: bool = False) -> dict:
        """ Return maximized geom.
        geom (dict): var to return maximized geometry.
        gaps (dict): dict to define useless gaps.
        byX (bool): maximize by X.
        byY (bool): maximize by Y. """
        if gaps == {}:
            gaps = self.useless_gaps
        if byX:
            geom['x'] = 0 + gaps['a']
            geom['width'] = self.current_resolution['width'] - gaps['d'] * 2
        if byY:
            geom['y'] = 0 + gaps['w']
            geom['height'] = self.current_resolution['height'] - gaps['s'] * 2
        return geom

    @staticmethod
    def set_geom(win, geom: dict) -> dict:
        """ Generic function to set geometry
        win: target window to change windows
        geom (dict): geometry. """
        win.command(f"move absolute position {geom['x']} {geom['y']}")
        win.command(f"resize set {geom['width']} {geom['height']} px")

    @staticmethod
    def set_resize_params_single(direction, amount):
        """ Set resize parameters for the single window """
        if direction == "natural":
            direction = "horizontal"
        elif direction == "orthogonal":
            direction = "vertical"
        if int(amount) < 0:
            mode = "plus"
            amount = -amount
        else:
            mode = "minus"
        return direction, mode, int(amount)

    @staticmethod
    def set_resize_params_multiple(direction, amount, vertical):
        """ Set resize parameters for the block of windows """
        mode = ""
        if direction == "horizontal":
            direction = "width"
        elif direction == "vertical":
            direction = "height"
        elif direction == "natural":
            direction = "height" if vertical else "width"
        elif direction == "orthogonal":
            direction = "width" if vertical else "height"
        elif direction == "top":
            direction = "up"
        elif direction == "bottom":
            direction = "down"
        if int(amount) < 0:
            mode = "shrink"
            amount = -int(amount)
        else:
            mode = "grow"
        return direction, mode, int(amount)

    def resize(self, direction, amount):
        """ Resize the current container along to the given direction. If there
        is only a single container, resize by adjusting gaps. If the direction
        is "natural", resize vertically in a splitv container, else
        horizontally. If it is "orhtogonal", do the opposite. """
        if direction not in [
                "natural", "orthogonal", "horizontal", "vertical",
                "top", "bottom", "left", "right",
                ]:
            try:
                amount = int(amount)
            except ValueError:
                print("Bad resize amount given.")
                return
        node = self.i3ipc.get_tree().find_focused()
        single, vertical = True, False
        # Check if there is only a single leaf.
        # If not, check if the curent container is in a vertical split.
        while True:
            parent = node.parent
            if node.type == "workspace" or not parent:
                break
            if parent.type == "floating_con":
                single = False
                break
            if len(parent.nodes) > 1 and parent.layout == "splith":
                single = False
                break
            if len(parent.nodes) > 1 and parent.layout == "splitv":
                single = False
                vertical = True
                break
            node = parent
        if single:
            direction, mode, amount = self.set_resize_params_single(
                direction, amount
            )
            self.i3ipc.command(f"gaps {direction} current {mode} {amount}")
        else:
            direction, mode, amount = self.set_resize_params_multiple(
                direction, amount, vertical
            )
            self.i3ipc.command(
                f"resize {mode} {direction} {amount} px or {amount//16} ppt"
            )

    @staticmethod
    def create_geom_from_rect(rect) -> dict:
        """ Create geometry from the given rectangle.
            rect: rect to extract geometry from. """
        geom = {}
        geom['x'] = rect.x
        geom['y'] = rect.y
        geom['height'] = rect.height
        geom['width'] = rect.width
        return geom

    def save_geom(self, target_win=None) -> dict:
        """ Save geometry.
        target_win: [optional] denotes target window. """
        if target_win is None:
            target_win = self.current_win
        return actions.create_geom_from_rect(target_win.rect)

    @staticmethod
    def focused_order(node):
        """ Iterate through the children of "node" in most recently focused
        order. """
        for focus_id in node.focus:
            return next(n for n in node.nodes if n.id == focus_id)

    @staticmethod
    def focused_child(node):
        """Return the most recently focused child of "node"."""
        return next(actions.focused_order(node))

    @staticmethod
    def is_in_line(old, new, direction):
        """ Return true if container "new" can reasonably be considered to be
        in direction of container "old" """
        if direction in {"up", "down"}:
            return new.rect.x <= old.rect.x + old.rect.width*0.9 \
                and new.rect.x + new.rect.width >= \
                old.rect.x + old.rect.width * 0.1

        if direction in {"left", "right"}:
            return new.rect.y <= old.rect.y + old.rect.height*0.9 \
                and new.rect.y + new.rect.height >= \
                old.rect.y + old.rect.height * 0.1

        return None

    def output_in_direction(self, output, window, direction):
        """ Return the output in direction "direction" of window "window" on
        output """
        tree = self.i3ipc.get_tree().find_focused()
        for new in self.focused_order(tree):
            if new.name == "__i3":
                continue
            if not self.is_in_line(window, new, direction):
                continue
            orct = output.rect
            nrct = new.rect
            if (direction == "left" and nrct.x + nrct.width == orct.x) \
                or (direction == "right" and nrct.x == orct.x + orct.width) \
                or (direction == "up" and nrct.y + nrct.height == orct.y) \
                or (direction == "down" and nrct.y == orct.y + orct.height):
                return new
        return None

    def focus_tab(self, direction) -> None:
        """ Cycle through the innermost stacked or tabbed ancestor container,
        or through floating containers. """
        if direction == "next":
            delta = 1
        elif direction == "prev":
            delta = -1
        else:
            return
        tree = self.i3ipc.get_tree()
        node = tree.find_focused()
        # Find innermost tabbed or stacked container, or detect floating.
        while True:
            parent = node.parent
            if not parent or node.type != "con":
                return
            if parent.layout in {"tabbed", "stacked"} \
                    or parent.type == "floating_con":
                break
            node = parent
        if parent.type == "floating_con":
            node = parent
            parent = node.parent
            # The order of floating_nodes is not useful, sort it somehow.
            parent_nodes = sorted(parent.floating_nodes, key=lambda n: n.id)
        else:
            parent_nodes = parent.nodes
        index = parent_nodes.index(node)
        node = parent_nodes[(index + delta) % len(parent_nodes)]
        # Find most recently focused leaf in new tab.
        while node.nodes:
            node = self.focused_child(node)
        self.i3ipc.command(f'[con_id="{node.id}"] focus')

    def visible_ws(self):
        result = []
        for ws in self.i3ipc.get_workspaces():
            if ws.visible:
                result.append(ws)
        return result

    def next_ws(self):
        focused = None
        ws_list = self.visible_ws()
        ws_numbers = []
        for ws in ws_list:
            if ws.focused == True:
                focused = ws
                break
        ws_index = None
        if focused is not None:
            for index, ws in enumerate(ws_list):
                if ws.name == focused.name:
                    ws_index = index
                    break
            next_ws_name = ""
            if ws_index + 1 >= len(ws_list):
                for ws in self.i3ipc.get_workspaces():
                    ws_numbers.append(ws.num)
                ws_numbers.sort()
                for i in range(focused.num + 1, ws_numbers[-1]):
                    if i not in ws_numbers:
                        next_ws_name = str(i) + ' :: ws'
                        break
                next_ws_name =  str(ws_numbers[-1] + 1) + ' :: ws'
            else:
                next_ws_name = ws_list[ws_index + 1]
            self.i3ipc.command("workspace " + next_ws_name)

    def move_tab(self, direction):
        """ Move the innermost stacked or tabbed ancestor container. """
        if direction == "next":
            delta = 1
        elif direction == "prev":
            delta = -1
        else:
            return
        node = self.i3ipc.get_tree().find_focused()
        # Find innermost tabbed or stacked container.
        while True:
            parent = node.parent
            if not parent or node.type != "con":
                return
            if parent.layout in ["tabbed", "stacked"]:
                break
            node = parent
        index = parent.nodes.index(node)
        if 0 <= index + delta < len(parent.nodes):
            other = parent.nodes[index + delta]
            self.i3ipc.command(
                f'[con_id="{node.id}"] swap container with con_id {other.id}'
            )

    def auto_tiling(self, _i3, _event):
        try:
            con = self.i3ipc.get_tree().find_focused()
            if con:
                # We're on i3: on sway it would be None
                if con.floating:
                    # May be 'auto_on' or 'user_on'
                    is_floating = '_on' in con.floating
                    is_full_screen = con.fullscreen_mode == 1
                # We are on sway
                else:
                    is_floating = con.type == 'floating_con'
                    # On sway on 1st focus the parent container returns 1, then
                    # forever the focused container itself
                    is_full_screen = con.fullscreen_mode == 1 or \
                        con.parent.fullscreen_mode == 1
                is_stacked = con.parent.layout == 'stacked'
                is_tabbed = con.parent.layout == 'tabbed'
                # Let's exclude floating containers, stacked layouts, tabbed
                # layouts and full screen mode
                if not is_floating and not is_stacked and \
                   not is_tabbed and not is_full_screen:
                    new_layout = 'splitv' if con.rect.height > con.rect.width \
                        else 'splith'
                    if new_layout != con.parent.layout:
                        self.i3ipc.command(new_layout)
        except Exception as exception:
            print(f'Error: {exception}', file=sys.stderr)
