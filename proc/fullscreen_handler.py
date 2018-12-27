#!/usr/bin/pypy3
""" Module to set / unset dpms while fullscreen is toggled on.

I am simply use xset here. There is better solution possible,
for example wayland-friendly.
"""

import i3ipc
from subprocess import run, Popen
import os
import sys
sys.path.append(os.getenv("XDG_CONFIG_HOME") + "/i3")
sys.path.append(os.getenv("XDG_CONFIG_HOME") + "/i3/lib")
from singleton import Singleton
from locker import get_lock
from basic_config import modconfig


class fullscreen_handler(Singleton, modconfig):
    def __init__(self, i3, loop=None):
        # i3ipc connection, bypassed by negi3mods runner
        self.i3 = i3ipc.Connection()
        self.panel_should_be_restored = False

        # Initialize modcfg.
        super().__init__(loop)

        cfg = self.cfg

        # default panel classes
        self.panel_classes = cfg.get("panel_classes", [])

        # fullscreened workspaces
        self.ws_fullscreen = cfg.get("ws_fullscreen", [])

        # for which windows we shoudn't show panel
        self.classes_to_hide_panel = cfg.get(
            "classes_to_hide_panel", []
        )

        self.panel_use_xdo = lambda act: run(['xdo', act, '-N', 'Polybar'])
        self.panel_use_polybar = lambda act: run(['polybar-msg', 'cmd', act])

        self.panel_use = self.panel_use_xdo

        self.i3.on('window::fullscreen_mode', self.on_fullscreen_mode)
        self.i3.on('window::close', self.on_window_close)
        self.i3.on('workspace::focus', self.on_focus)

    def on_focus(self, i3, event):
        i3_tree = i3.get_tree()
        focused_win = i3_tree.find_focused()
        fullscreens = i3_tree.find_fullscreen()
        for w in fullscreens:
            if w.id == focused_win.id:
                for ws_name in self.ws_fullscreen:
                    if ws_name in event.current.name:
                        self.panel_action('hide', restore=True)
                        return

        for ws_name in self.ws_fullscreen:
            if ws_name in event.old.name and ws_name not in event.current.name:
                if self.panel_should_be_restored:
                    self.panel_action('show', restore=False)
                    return

    def panel_action(self, action, restore):
        self.panel_use(action)
        if restore is not None:
            self.panel_should_be_restored = restore

    def on_fullscreen_mode(self, i3, event):
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
                                self.panel_action('hide', restore=True)
                                break
                        return

    def on_window_close(self, i3, event):
        """ Check the current fullscreen window, if no fullscreen enable dpms.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        if event.container.window_class in self.panel_classes:
            return

        if not i3.get_tree().find_fullscreen():
            self.panel_action('hide', restore=True)


if __name__ == '__main__':
    get_lock('fullscreen_handler.py')
    i3 = i3ipc.Connection()
    proc = fullscreen_handler(i3)
    proc.i3.main()

