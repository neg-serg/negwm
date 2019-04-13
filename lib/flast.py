""" Advanced alt-tab module.

This module allows you to focus previous window a-la "alt-tab" not by workspace
but by window itself. To achieve that I am using self.window_history to store
information about previous windows. We need this because previously selected
window may be closed, and then you cannot focus it.
"""

from typing import List, Iterator
from singleton import Singleton
from main import find_visible_windows
from modi3cfg import modi3cfg
from collections import deque
from itertools import cycle


class flast(modi3cfg):
    """ Advanced alt-tab class.

    Metaclass:
        Use Singleton metaclass from singleton module.

    """
    __metaclass__ = Singleton

    def __init__(self, i3, loop=None) -> None:
        """ Init function

        Args:
            i3: i3ipc connection
            loop: asyncio loop. It's need to be given as parameter because of
                  you need to bypass asyncio-loop to the thread
        """
        # Initialize modi3cfg.
        modi3cfg.__init__(self, i3)

        # i3ipc connection, bypassed by negi3mods runner
        self.i3 = i3

        # previous / current window list
        self.window_history = []

        # depth of history list
        self.max_win_history = 64

        # workspaces with auto alt-tab when close
        self.autoback = self.conf('autoback')

        self.i3.on('window::focus', self.on_window_focus)
        self.i3.on('window::close', self.goto_nonempty_ws_on_close)

    def reload_config(self) -> None:
        """ Reloads config. Dummy.
        """
        self.__init__(self.i3)

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
            "switch": self.alt_tab,
            "reload": self.reload_config,
            "focus_next": self.focus_next,
            "focus_prev": self.focus_prev,
            "focus_next_visible": self.focus_next_visible,
            "focus_prev_visible": self.focus_prev_visible,
        }[args[0]](*args[1:])

    def alt_tab(self) -> None:
        """ Focus previous window.
        """
        wids = set(w.id for w in self.i3.get_tree().leaves())
        for wid in self.window_history[1:]:
            if wid not in wids:
                self.window_history.remove(wid)
            else:
                self.i3.command(f'[con_id={wid}] focus')
                return

    def on_window_focus(self, i3, event) -> None:
        """ Store information about current / previous windows.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        wid = event.container.id

        if wid in self.window_history:
            self.window_history.remove(wid)

        self.window_history.insert(0, wid)
        if len(self.window_history) > self.max_win_history:
            del self.window_history[self.max_win_history:]

    def get_windows_on_ws(self) -> Iterator:
        """ Get windows on the current workspace.
        """
        return filter(
            lambda x: x.window,
            self.i3.get_tree().find_focused().workspace().descendents()
        )

    def goto_visible(self, reversed_order = False):
        """ Focus next visible window.

        Args:
            reversed_order(bool) : [optional] predicate to change order.

        """
        wins = find_visible_windows(self.get_windows_on_ws())
        self.goto_win(wins, reversed_order)

    def goto_win(self, wins, reversed_order = False):
        if reversed_order:
            cycle_windows = cycle(reversed(wins))
        else:
            cycle_windows = cycle(wins)
        for window in cycle_windows:
            if window.focused:
                focus_to = next(cycle_windows)
                self.i3.command('[id="%d"] focus' % focus_to.window)
                break

    def goto_any(self, reversed_order: bool = False) -> None:
        """ Focus any next window.

        Args:
            reversed_order(bool) : [optional] predicate to change order.
        """
        wins = self.i3.get_tree().leaves()
        self.goto_win(wins, reversed_order)

    def focus_next(self) -> None:
        self.goto_any(reversed_order=False)

    def focus_prev(self) -> None:
        self.goto_any(reversed_order=True)

    def focus_next_visible(self) -> None:
        self.goto_visible(reversed_order=False)

    def focus_prev_visible(self) -> None:
        self.goto_visible(reversed_order=True)

    def goto_nonempty_ws_on_close(self, i3, event) -> None:
        """ Go back for temporary tags like pictures or media.

            This function make auto alt-tab for workspaces which should by
            temporary. This is good if you do not want to see empty workspace
            after switching to the media content workspace.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        workspace = i3.get_tree().find_focused().workspace()
        focused_ws_name = workspace.name
        wswins = workspace.descendents()
        if not len(wswins):
            for ws_substr in self.autoback:
                if focused_ws_name.endswith(ws_substr):
                    self.i3.command('workspace back_and_forth')

