#!/usr/bin/pypy3
""" Module to set / unset dpms while fullscreen is toggled on.

I am simply use xset here. There is better solution possible,
for example wayland-friendly.
"""

import subprocess
from typing import List
from negi3mod import negi3mod
from cfg import cfg


class fs(negi3mod, cfg):
    def __init__(self, i3, loop=None):
        # i3ipc connection, bypassed by negi3mods runner
        self.i3 = i3
        self.panel_should_be_restored = False

        # Initialize modcfg.
        cfg.__init__(self, i3, convert_me=False)

        # default panel classes
        self.panel_classes = self.cfg.get("panel_classes", [])

        # fullscreened workspaces
        self.ws_fullscreen = self.cfg.get("ws_fullscreen", [])

        # for which windows we shoudn't show panel
        self.classes_to_hide_panel = self.cfg.get(
            "classes_to_hide_panel", []
        )

        self.show_panel_on_close = False

        self.bindings = {
            "reload": self.reload_config,
            "fullscreen": self.fullscreen_hide,
        }

        self.i3.on('window::close', self.on_window_close)
        self.i3.on('workspace::focus', self.on_workspace_focus)

    def on_workspace_focus(self, i3, event):
        for tgt_ws in self.ws_fullscreen:
            if event.current.name.endswith(tgt_ws):
                self.panel_action('hide', restore=False)
                return

        for tgt_ws in self.ws_fullscreen:
            if not event.current.name.endswith(tgt_ws):
                self.panel_action('show', restore=False)
                return

    def panel_action(self, action, restore):
        proc = subprocess.Popen(
            ['xdo', action, '-N', 'Polybar'], stdout=subprocess.PIPE
        )
        proc.communicate()[0]

        if restore is not None:
            self.panel_should_be_restored = restore

    def on_fullscreen_mode(self, i3, event):
        """ Disable panel if it was in fullscreen mode and then goes to
        windowed mode.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        if event.container.window_class in self.panel_classes:
            return

        self.fullscreen_hide(i3)

    def fullscreen_hide(self):
        i3_tree = self.i3.get_tree()
        fullscreens = i3_tree.find_fullscreen()
        focused_ws = i3_tree.find_focused().workspace().name

        if fullscreens:
            for win in fullscreens:
                for tgt_class in self.classes_to_hide_panel:
                    if win.window_class == tgt_class:
                        for tgt_ws in self.ws_fullscreen:
                            if focused_ws.endswith(tgt_ws):
                                self.panel_action('hide', restore=False)
                                break

    def on_window_close(self, i3, event):
        """ If there are no fullscreen windows then show panel closing window.

            Args:
                i3: i3ipc connection.
                event: i3ipc event. We can extract window from it using
                event.container.
        """
        if event.container.window_class in self.panel_classes:
            return

        if self.show_panel_on_close:
            if not i3.get_tree().find_fullscreen():
                self.panel_action('show', restore=True)

