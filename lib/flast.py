""" Advanced alt-tab module.

This module allows you to focus previous window a-la "alt-tab" not by workspace
but by window itself. To achieve that I am using self.window_history to store
information about previous windows. We need this because previously selected
window may be closed, and then you cannot focus it.
"""

from typing import List
from main import find_visible_windows
from singleton import Singleton
from modi3cfg import modi3cfg


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
        self.i3.on('window::close', self.go_back_if_nothing)

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
        }[args[0]](*args[1:])

    def alt_tab(self) -> None:
        """ Focus previous window.
        """
        leaves = self.i3.get_tree().leaves()
        for wid in self.window_history[1:]:
            if wid not in set(w.id for w in leaves):
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

    def go_back_if_nothing(self, i3, event) -> None:
        """ Go back for temporary tags like pictures or media.

            This function make auto alt-tab for workspaces which should by
            temporary. This is good if you do not want to see empty workspace
            after switching to the media content workspace.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        focused_ws_name = i3.get_tree().find_focused().workspace().name
        wswins = filter(
            lambda win: win.window,
                i3.get_tree()
                .find_focused()
                .workspace()
                .descendents()
        )
        if not len(find_visible_windows(wswins)):
            for ws_substr in self.autoback:
                if focused_ws_name.endswith(ws_substr):
                    self.alt_tab()
                    return

