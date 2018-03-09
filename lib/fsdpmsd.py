from subprocess import call
from singleton import Singleton
import i3ipc


class fsdpms(Singleton):
    def __init__(self, i3):
        self.i3 = i3
        self.i3.on('window::fullscreen_mode', self.on_fullscreen_mode)
        self.i3.on('window::close', self.on_window_close)

    def set_dpms(self, state):
        if state:
            call(['xset', 's', 'on'])
            call(['xset', '+dpms'])
        else:
            call(['xset', 's', 'off'])
            call(['xset', '-dpms'])

    def on_fullscreen_mode(self, i3, event):
        self.set_dpms(
            not len(self.i3.get_tree().find_fullscreen())
        )

    def on_window_close(self, i3, event):
        if not len(self.i3.get_tree().find_fullscreen()):
            self.set_dpms(True)

