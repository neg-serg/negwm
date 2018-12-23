#!/usr/bin/pypy3
""" Module to set / unset dpms while fullscreen is toggled on.

I am simply use xset here. There is better solution possible,
for example wayland-friendly.
"""

import subprocess
from singleton import Singleton


class fullscreen_handler(Singleton):
    __metaclass__ = Singleton

    def __init__(self, i3, cfg):

        self.panel_should_be_restored = False

        # default panel classes
        self.panel_classes = cfg.panel_classes

        # fullscreened workspaces
        self.ws_fullscreen = cfg.ws_fullscreen

        # for which windows we shoudn't show panel
        self.classes_to_hide_panel = cfg.classes_to_hide_panel

        self.set_panel_xdo = lambda action: subprocess.Popen(
            ['xdo', action, '-N', 'Polybar']
        )

        self.set_panel_polybar = lambda action: subprocess.Popen(
            ['polybar-msg', 'cmd', action]
        )

        self.panel_action = self.set_panel_xdo

    def set_panel(self, action, restore):
        self.panel_action(action)
        if restore is not None:
            self.panel_should_be_restored = restore

    # call it on window focus
    def focus_action(self, i3, event):
        i3_tree = i3.get_tree()
        focused_win = i3_tree.find_focused()
        fullscreens = i3_tree.find_fullscreen()
        for w in fullscreens:
            if w.id == focused_win.id:
                for ws_name in self.ws_fullscreen:
                    if ws_name in event.current.name:
                        self.set_panel('hide', restore=True)
                        return

        for ws_name in self.ws_fullscreen:
            if ws_name in event.old.name and ws_name not in event.current.name:
                if self.panel_should_be_restored:
                    self.set_panel('show', restore=False)
                    return

    # call it on window close
    def window_close_action(self, i3, event):
        """ Check the current fullscreen window, if no fullscreen enable dpms.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        if event.container.window_class in self.panel_classes:
            return

        if not i3.get_tree().find_fullscreen():
            self.set_panel('show')

    # call it on fullscreen mode
    def fullscreen_toggle_action(self, i3, event):
        """ Disable fullscreen if fullscreened window is here.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        if event.container.window_class in self.panel_classes:
            return

        i3_tree = i3.get_tree()
        fullscreens = i3_tree.find_fullscreen()

        if fullscreens:
            focused_ws = i3_tree.find_focused().workspace().name
            for win in fullscreens:
                for tgt_class in self.classes_to_hide_panel:
                    if win.window_class == tgt_class:
                        for ws in self.ws_fullscreen:
                            if ws in focused_ws:
                                self.set_panel('hide', restore=True)
                                break
                        return

