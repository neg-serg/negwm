import lib.i3ipc as i3ipc
from threading import Thread
from subprocess import run
from singleton import Singleton


class fsdpms(Singleton):
    def __init__(self, i3, loop=None):
        self.i3 = i3ipc.Connection()
        self.i3.on('window::fullscreen_mode', self.on_fullscreen_mode)
        self.i3.on('window::close', self.on_window_close)
        Thread(target=self.i3.main, daemon=True).start()

    def set_dpms(self, state):
        if state:
            run(['xset', 's', 'on'])
            run(['xset', '+dpms'])
        else:
            run(['xset', 's', 'off'])
            run(['xset', '-dpms'])

    def on_fullscreen_mode(self, i3, event):
        tree = self.i3.get_tree()
        self.set_dpms(
            not len(tree.find_fullscreen())
        )

    def on_window_close(self, i3, event):
        tree = self.i3.get_tree()
        if not len(tree.find_fullscreen()):
            self.set_dpms(True)

