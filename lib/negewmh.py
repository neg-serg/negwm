""" In this module we have EWMH routines to detect dialog windows, visible windows,
etc using python-xlib and python-ewmh. """
from typing import List
from contextlib import contextmanager

import Xlib
import Xlib.display
from ewmh import EWMH


class NegEWMH():
    """ Custom EWMH support functions """
    disp = Xlib.display.Display()
    ewmh = EWMH()

    @staticmethod
    @contextmanager
    def window_obj(disp, win_id):
        """ Simplify dealing with BadWindow (make it either valid or None) """
        window_obj = None
        if win_id:
            try:
                window_obj = disp.create_resource_object('window', win_id)
            except Xlib.error.XError:
                pass
        yield window_obj

    @staticmethod
    def is_dialog_win(win) -> bool:
        """ Check that window [win] is not dialog window
        At first check typical window roles and classes, because of it more
        fast, then using python EWMH module to detect dialog window type or
        modal state of window.
        win : target window to check """
        if win.window_instance == "Places" \
                or win.window_role in {
                        "GtkFileChooserDialog",
                        "confirmEx",
                        "gimp-file-open"} \
                or win.window_class == "Dialog":
            return True
        with NegEWMH.window_obj(NegEWMH.disp, win.window) as win_obj:
            win_type = NegEWMH.ewmh.getWmWindowType(win_obj, str=True)
            if '_NET_WM_WINDOW_TYPE_DIALOG' in win_type:
                return True
            win_state = NegEWMH.ewmh.getWmState(win_obj, str=True)
            if '_NET_WM_STATE_MODAL' in win_state:
                return True
            return False

    @staticmethod
    def find_visible_windows(windows_on_ws: List) -> List:
        """ Find windows visible on the screen now.
        windows_on_ws: windows list which going to be filtered with this
        function. """
        visible_windows = []
        for win in windows_on_ws:
            with NegEWMH.window_obj(NegEWMH.disp, win.window) as win_obj:
                win_state = NegEWMH.ewmh.getWmState(win_obj, str=True)
                if '_NET_WM_STATE_HIDDEN' not in win_state:
                    visible_windows.append(win)
        return visible_windows
