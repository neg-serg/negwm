#!/usr/bin/pypy3
""" Module to set / unset dpms while fullscreen is toggled on.

I am simply use xset here. There is better solution possible,
for example wayland-friendly.
"""

import i3ipc
from subprocess import run
import os
import sys
from collections import deque
sys.path.append(os.getenv("XDG_CONFIG_HOME") + "/i3")
sys.path.append(os.getenv("XDG_CONFIG_HOME") + "/i3/lib")
from singleton import Singleton
from locker import get_lock


class fullscreen_handler(Singleton):
    def __init__(self, i3, loop=None):
        # i3ipc connection, bypassed by negi3mods runner
        self.i3 = i3ipc.Connection()
        self.polybar_need_restore = False
        self.focused_wins = deque(maxlen=10)

        self.i3.on('window::fullscreen_mode', self.on_fullscreen_mode)
        self.i3.on('window::close', self.on_window_close)
        self.i3.on('workspace::focus', self.on_focus)

    def on_focus(self, i3, event):
        if 'media' in event.old.name and 'media' not in event.current.name:
            if self.polybar_need_restore:
                self.set_polybar(True)
                self.polybar_need_restore = False

    def set_polybar(self, on):
        if on:
            run(['polybar-msg', 'cmd', 'show'])
        else:
            run(['polybar-msg', 'cmd', 'hide'])
        pass

    def set_dpms(self, on):
        """ set / unset dpms
        """
        if on:
            run(['xset', 's', 'on'])
            run(['xset', '+dpms'])
        else:
            run(['xset', 's', 'off'])
            run(['xset', '-dpms'])

    def on_fullscreen_mode(self, i3, event):
        """ Disable fullscreen if fullscreened window is here.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        if event.container.window_class == 'polybar':
            return
        tree = self.i3.get_tree()
        fullscreens = tree.find_fullscreen()
        self.set_dpms(not fullscreens)
        if fullscreens:
            for win in fullscreens:
                if win.window_class == 'mpv':
                    self.set_polybar(False)
                    self.polybar_need_restore = True

    def on_window_close(self, i3, event):
        """ Check the current fullscreen window, if no fullscreen enable dpms.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        if event.container.window_class == 'polybar':
            return
        tree = self.i3.get_tree()
        fullscreens = tree.find_fullscreen()
        if not fullscreens:
            self.set_dpms(True)
            self.set_polybar(True)


if __name__ == '__main__':
    get_lock('fullscreen_handler.py')
    i3 = i3ipc.Connection()
    proc = fullscreen_handler(i3)
    proc.i3.main()

