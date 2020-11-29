""" Module to set / unset dpms while fullscreen is toggled on. I am simply use
xset here. There is better solution possible, for example wayland-friendly. """

import subprocess
import shutil
from extension import extension
from cfg import cfg

class fullscreen(extension, cfg):
    def __init__(self, i3conn):
        # i3ipc connection, bypassed by negi3wm runner
        self.i3ipc = i3conn
        self.panel_should_be_restored = False
        cfg.__init__(self, i3conn) # Initialize modcfg.
        # Default panel classes
        self.panel_classes = self.cfg.get("panel_classes", [])
        # Fullscreened workspaces
        self.ws_fullscreen = self.cfg.get("ws_fullscreen", [])
        # for which windows we shoudn't show panel
        self.classes_to_hide_panel = self.cfg.get(
            "classes_to_hide_panel", []
        )
        self.show_panel_on_close = False
        self.bindings = {
            "reload": self.reload_config,
            "fullscreen": self.hide,
        }
        self.i3ipc.on('window::close', self.on_window_close)
        self.i3ipc.on('workspace::focus', self.on_workspace_focus)

    def on_workspace_focus(self, _, event):
        """ Hide panel if it is fullscreen workspace, show panel otherwise """
        for tgt_ws in self.ws_fullscreen:
            if event.current.name.endswith(tgt_ws):
                self.panel_action('hide', restore=False)
                return
        self.panel_action('show', restore=False)

    def panel_action(self, action: str, restore: bool):
        """ Helper to do show/hide with panel or another action
            action (str): action to do.
            restore(bool): shows should the panel state be restored or not. """
        ret = None
        try:
            ret = subprocess.Popen(
                ['xdo', action, '-N', 'Polybar'], stdout=subprocess.PIPE
            ).communicate()[0]
        except Exception:
            xdo_path = shutil.which('xdo')
            if xdo_path:
                print('xdo exists in {xdo_path}, but not working')
            else:
                print('There is no xdo, please install')
        if not ret and restore is not None:
            self.panel_should_be_restored = restore

    def on_fullscreen_mode(self, _, event):
        """ Disable panel if it was in fullscreen mode and then goes to
        windowed mode.
        _: i3ipc connection.
        event: i3ipc event. We can extract window from it using
        event.container. """
        if event.container.window_class in self.panel_classes:
            return
        self.hide()

    def hide(self):
        """ Hide panel for this workspace """
        i3_tree = self.i3ipc.get_tree()
        fullscreens = i3_tree.find_fullscreen()
        focused_ws = i3_tree.find_focused().workspace().name
        if not fullscreens:
            return
        for win in fullscreens:
            for tgt_class in self.classes_to_hide_panel:
                if win.window_class == tgt_class:
                    for tgt_ws in self.ws_fullscreen:
                        if focused_ws.endswith(tgt_ws):
                            self.panel_action('hide', restore=False)
                            break

    def on_window_close(self, i3conn, event):
        """ If there are no fullscreen windows then show panel closing window.
        i3: i3ipc connection.
        event: i3ipc event. We can extract window from it using
        event.container. """
        if event.container.window_class in self.panel_classes:
            return
        if self.show_panel_on_close:
            if not i3conn.get_tree().find_fullscreen():
                self.panel_action('show', restore=True)
