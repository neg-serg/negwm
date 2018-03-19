""" Module to set / unset dpms while fullscreen is toggled on.

I am simply use xset here. There is better solution possible,
for example wayland-friendly.
"""

import i3ipc
from threading import Thread
from subprocess import run
from singleton import Singleton


class fsdpms(Singleton):
    def __init__(self, i3, loop=None):
        # i3ipc connection, bypassed by negi3mods runner
        self.i3 = i3ipc.Connection()

        self.i3.on('window::fullscreen_mode', self.on_fullscreen_mode)
        self.i3.on('window::close', self.on_window_close)

        Thread(target=self.i3.main, daemon=True).start()

    def set_dpms(self, state):
        """ set / unset dpms
        """
        if state:
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
        tree = self.i3.get_tree()
        self.set_dpms(not tree.find_fullscreen())

    def on_window_close(self, i3, event):
        """ Check the current fullscreen window, if no fullscreen enable dpms.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        tree = self.i3.get_tree()
        if not tree.find_fullscreen():
            self.set_dpms(True)

