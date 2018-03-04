from subprocess import check_output
from itertools import cycle
from singleton import Singleton
import i3ipc


class wm3(Singleton):
    def __init__(self):
        self.i3 = i3ipc.Connection()

    def switch(self, args):
        {
            "reload": self.reload_config,
            "focus_next_visible": self.focus_next_visible,
            "focus_prev_visible": self.focus_prev_visible,
        }[args[0]](*args[1:])

    def reload_config(self):
        self.__init__()

    def get_windows_on_ws(self):
        return filter(
            lambda x: x.window,
            self.i3.get_tree().find_focused().workspace().descendents()
        )

    def find_visible_windows(self, windows_on_ws):
        visible_windows = []
        for w in windows_on_ws:
            try:
                xprop = check_output(['xprop', '-id', str(w.window)]).decode()
            except FileNotFoundError:
                raise SystemExit("The `xprop` utility is not found!"
                                 " Please install it and retry.")

            if '_NET_WM_STATE_HIDDEN' not in xprop:
                visible_windows.append(w)

        return visible_windows

    def focus_next(self, reversed_order=False):
        visible_windows = self.find_visible_windows(self.get_windows_on_ws())
        if reversed_order:
            cycle_windows = cycle(reversed(visible_windows))
        else:
            cycle_windows = cycle(visible_windows)
        for window in cycle_windows:
            if window.focused:
                focus_to = next(cycle_windows)
                self.i3.command('[id="%d"] focus' % focus_to.window)
                break

    def focus_prev_visible(self):
        self.focus_next(reversed_order=True)

    def focus_next_visible(self):
        self.focus_next()

