from modlib import find_visible_windows
from singleton import Singleton


class flast():
    __metaclass__ = Singleton

    def __init__(self, i3):
        self.i3 = i3
        self.window_list = self.i3.get_tree().leaves()
        self.max_win_history = 64
        self.i3.on('window::focus', self.on_window_focus)
        self.i3.on('window::close', self.go_back_if_nothing)

    def reload_config(self):
        self.__init__(self.i3)

    def switch(self, args):
        {
            "switch": self.alt_tab,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def alt_tab(self):
        for wid in self.window_list[1:]:
            if wid not in set(w.id for w in self.i3.get_tree().leaves()):
                self.window_list.remove(wid)
            else:
                self.i3.command(f'[con_id={wid}] focus')
                return

    def on_window_focus(self, i3, event):
        wid = event.container.id

        if wid in self.window_list:
            self.window_list.remove(wid)

        self.window_list.insert(0, wid)
        if len(self.window_list) > self.max_win_history:
            del self.window_list[self.max_win_history:]

    def get_windows_on_ws(self):
        return filter(
            lambda win: win.window,
            self.i3.get_tree().find_focused().workspace().descendents()
        )

    def go_back_if_nothing(self, i3, event):
        focused = i3.get_tree().find_focused()
        wswins = filter(
            lambda win: win.window,
            self.i3.get_tree().find_focused().workspace().descendents()
        )
        if not len(find_visible_windows(wswins)):
            for ws in ["pic", "media"]:
                if ws in focused.workspace().name:
                    self.alt_tab()
                    return

