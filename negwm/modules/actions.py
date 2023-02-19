""" 2bwm-like features module.
There are a lot of various actions over the floating windows in this module,
which may reminds you 2bwm, subtle, or another similar window managers. You can
change window geometry, move it to the half or quad size of the screen space,
etc. Partially code is taken from https://github.com/miseran/i3-tools, thanks
to you, miseran(https://github.com/miseran)
"""

import collections
from typing import Mapping
import logging

from negwm.lib.display import Display
from negwm.lib.cfg import cfg
from negwm.lib.extension import extension

# # Grid floating windows
# mode "i3grid" {
#     bindsym q exec "python3 -m i3grid snap --cols 2 --rows 2 --target 1"
#     bindsym e exec "python3 -m i3grid snap --cols 2 --rows 2 --target 2"
#     bindsym z exec "python3 -m i3grid snap --cols 2 --rows 2 --target 3"
#     bindsym c exec "python3 -m i3grid snap --cols 2 --rows 2 --target 4"
#
#     bindsym w exec "python3 -m i3grid snap --cols 1 --rows 2 --target 1"
#     bindsym x exec "python3 -m i3grid snap --cols 1 --rows 2 --target 2"
#
#     bindsym a exec "python3 -m i3grid snap --cols 2 --rows 1 --target 1"
#     bindsym d exec "python3 -m i3grid snap --cols 2 --rows 1 --target 2"
#     bindsym s exec "python3 -m i3grid reset"
#     bindsym f exec "python3 -m i3grid csize --perc 100"
#
#     bindsym g exec "python3 -m i3grid csize --perc 33"
#     bindsym h exec "python3 -m i3grid csize --perc 50"
#     bindsym j exec "python3 -m i3grid csize --perc 66"
#     bindsym k exec "python3 -m i3grid csize --perc 85"
#     bindsym l exec "python3 -m i3grid csize --perc 92"
#     bindsym p exec "python3 -m i3grid snap --cols 3 --rows 3 --target 3"
#     bindsym o exec "python3 -m i3grid snap --cols 3 --rows 3 --target 2"
#     bindsym i exec "python3 -m i3grid snap --cols 3 --rows 3 --target 1"
#
#     bindsym Return mode "default"
#     bindsym Escape mode "default"
#     bindsym m mode "default"
#     bindsym n mode "default"
# }
# bindsym $mod+shift+o mode "i3grid"


class actions(extension, cfg):
    def __init__(self, i3) -> None:
        """ Main part is in self.initialize,
        which performs initialization itself.
        i3: i3ipc connection """
        # Initialize cfg.
        cfg.__init__(self, i3)
        # i3ipc connection, bypassed by negwm runner.
        self.i3ipc = i3
        maxlength = self.conf('cache_list_size')  # cache list length
        # create list with the finite number of elements by the [None] * N hack
        self.geom_list = collections.deque([None] * maxlength, maxlen=maxlength)
        self.current_win = None
        # We need to know current resolution for almost all operations here.
        self.current_resolution = Display.get_screen_resolution()
        # Here we load information about useless gaps
        self.load_useless_gaps()
        # Coeff to grow window in all dimensions
        self.grow_coeff = self.conf('grow_coeff')
        # Coeff to shrink window in all dimensions
        self.shrink_coeff = self.conf('shrink_coeff')

    def load_useless_gaps(self) -> None:
        """ Load useless gaps settings. """
        try:
            if not self.cfg['useless_gaps']:
                self.useless_gaps = {"w": 0, "a": 0, "s": 0, "d": 0}
                return
            self.useless_gaps = self.cfg['useless_gaps']
            for field in ['w', 'a', 's', 'd']:
                if self.useless_gaps[field] < 0:
                    self.useless_gaps[field] = abs(self.useless_gaps[field])
        except (KeyError, TypeError, AttributeError):
            self.useless_gaps = {"w": 0, "a": 0, "s": 0, "d": 0}

    def get_prev_geom(self):
        """ Get previous window geometry. """
        self.geom_list.append({
            'id': self.current_win.id,
            'geom': self.save_geom()
        })
        return self.geom_list[-1]['geom']

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
        # Config about useless gaps for half splitting, True by default
        if self.conf('x2_use_gaps'):
            gaps = self.useless_gaps
        else:
            gaps = {'w': 0, 'a': 0, 's': 0, 'd': 0}
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
                max_geom = self.maximized_geom(geom.copy(), gaps={}, byX=True, byY=True)
            elif by == 'X':
                max_geom = self.maximized_geom(geom.copy(), gaps={}, byX=True, byY=False)
            elif by == 'Y':
                max_geom = self.maximized_geom(geom.copy(), gaps={}, byX=False, byY=True)
            actions.set_geom(self.current_win, max_geom)

    def revert_maximize(self) -> None:
        """ Revert changed window state. """
        try:
            focused = self.i3ipc.get_tree().find_focused()
            if self.geom_list[-1].get('geom', {}):
                actions.set_geom(focused, self.geom_list[-1]['geom'])
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
        match direction:
            case 'natural': direction = 'horizontal'
            case 'orthogonal': direction = 'vertical'
        if int(amount) < 0:
            mode = "plus"
            amount = -amount
        else:
            mode = "minus"
        return direction, mode, int(amount)

    def resize(self, direction, amount):
        """ Resize the current container along to the given direction. If there
        is only a single container, resize by adjusting gaps. If the direction
        is 'natural', resize vertically in a splitv container, else
        horizontally. If it is 'orhtogonal', do the opposite. """
        possible_directions = [
            'natural', 'orthogonal', 'horizontal', 'vertical',
            'top', 'bottom', 'left', 'right'
        ]
        if direction not in possible_directions:
            try:
                amount = int(amount)
            except ValueError:
                logging.error("Bad resize amount given.")
                return
        node = self.i3ipc.get_tree().find_focused()
        single, vertical = True, False
        # Check if there is only a single leaf.
        # If not, check if the curent container is in a vertical split.
        while True:
            parent = node.parent
            if node.type == 'workspace' or not parent:
                break
            if parent.type == 'floating_con':
                single = False
                break
            if len(parent.nodes) > 1 and parent.layout == 'splith':
                single = False
                break
            if len(parent.nodes) > 1 and parent.layout == 'splitv':
                single = False
                vertical = True
                break
            node = parent
        if single:
            direction, mode, amount = self.set_resize_params_single(
                direction, amount
            )
            self.i3ipc.command(f'gaps {direction} current {mode} {amount}')
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
        return {
            'x': rect.x,
            'y': rect.y,
            'height': rect.height,
            'width': rect.width
        }

    def save_geom(self, target_win=None) -> dict:
        """ Save geometry.
        target_win: [optional] denotes target window. """
        if target_win is None:
            target_win = self.current_win
        return actions.create_geom_from_rect(target_win.rect)

    @staticmethod
    def focused_order(node):
        """ Iterate through the children of 'node' in most recently focused
        order. """
        for focus_id in node.focus:
            return next(n for n in node.nodes if n.id == focus_id)

    @staticmethod
    def focused_child(node):
        """Return the most recently focused child of 'node'."""
        return next(actions.focused_order(node))

    @staticmethod
    def is_in_line(old, new, direction):
        """ Return true if container 'new' can reasonably be considered to be
        in direction of container 'old' """
        if direction in {'up', 'down'}:
            return new.rect.x <= old.rect.x + old.rect.width*0.9 \
                and new.rect.x + new.rect.width >= \
                old.rect.x + old.rect.width * 0.1
        if direction in {'left', 'right'}:
            return new.rect.y <= old.rect.y + old.rect.height*0.9 \
                and new.rect.y + new.rect.height >= \
                old.rect.y + old.rect.height * 0.1
        return None

    def output_in_direction(self, output, window, direction):
        """ Return the output in direction 'direction' of window 'window' on
        output """
        tree = self.i3ipc.get_tree().find_focused()
        for new in self.focused_order(tree):
            if new.name == '__i3':
                continue
            if not self.is_in_line(window, new, direction):
                continue
            orct = output.rect
            nrct = new.rect
            if (direction == 'left' and nrct.x + nrct.width == orct.x) \
                or (direction == 'right' and nrct.x == orct.x + orct.width) \
                or (direction == 'up' and nrct.y + nrct.height == orct.y) \
                or (direction == 'down' and nrct.y == orct.y + orct.height):
                return new
        return None

    def focus_tab(self, direction) -> None:
        """ Cycle through the innermost stacked or tabbed ancestor container,
        or through floating containers. """
        if direction == 'next':
            delta = 1
        elif direction == 'prev':
            delta = -1
        else:
            return
        tree = self.i3ipc.get_tree()
        node = tree.find_focused()
        # Find innermost tabbed or stacked container, or detect floating.
        while True:
            parent = node.parent
            if not parent or node.type != 'con':
                return
            if parent.layout in {'tabbed', 'stacked'} \
                    or parent.type == 'floating_con':
                break
            node = parent
        if parent.type == 'floating_con':
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
        ws_magic_pie = ' :: ws'
        focused = None
        ws_list = self.visible_ws()
        ws_numbers = []
        for ws in ws_list:
            if ws.focused == True:
                focused = ws
                break
        ws_index = 0
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
                        next_ws_name = f'{str(i)} {ws_magic_pie}'
                        break
                next_ws_name = f'{str(ws_numbers[-1] + 1)} {ws_magic_pie}'
            else:
                next_ws_name = ws_list[ws_index + 1]
            self.i3ipc.command(f'workspace {next_ws_name}')

    def move_tab(self, direction):
        """ Move the innermost stacked or tabbed ancestor container. """
        if direction == 'next':
            delta = 1
        elif direction == 'prev':
            delta = -1
        else:
            return
        node = self.i3ipc.get_tree().find_focused()
        # Find innermost tabbed or stacked container.
        while True:
            parent = node.parent
            if not parent or node.type != 'con':
                return
            if parent.layout in ['tabbed', 'stacked']:
                break
            node = parent
        index = parent.nodes.index(node)
        if 0 <= index + delta < len(parent.nodes):
            other = parent.nodes[index + delta]
            self.i3ipc.command(
                f'[con_id="{node.id}"] swap container with con_id {other.id}'
            )
