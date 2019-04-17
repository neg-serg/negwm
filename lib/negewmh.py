from typing import List
from contextlib import contextmanager

import Xlib
import Xlib.display
from ewmh import EWMH


class NegEWMH():
    disp = Xlib.display.Display()
    ewmh = EWMH()

    @contextmanager
    def window_obj(disp, win_id):
        """Simplify dealing with BadWindow (make it either valid or None)"""
        window_obj = None
        if win_id:
            try:
                window_obj = disp.create_resource_object('window', win_id)
            except Xlib.error.XError:
                pass
        yield window_obj

    def is_dialog_win(w) -> bool:
        """ Check that window [w] is not dialog window

            Unfortunately for now external xprop application used for it,
            because of i3ipc gives no information about what windows dialog or
            not, shown/hidden or about _NET_WM_STATE_HIDDEN attribute or
            "custom" window attributes, etc.

            Args:
                w : target window to check
        """
        if w.window_instance == "Places" \
                or w.window_role in {"GtkFileChooserDialog", "confirmEx",
                                     "gimp-file-open"} \
                or w.window_class == "Dialog":
            return True

        with NegEWMH.window_obj(NegEWMH.disp, w.window) as win:
            xprop = NegEWMH.ewmh.getWmWindowType(win, str=True)

            is_dialog = False
            for tok in xprop:
                if '_NET_WM_WINDOW_TYPE(ATOM)' in tok:
                    is_dialog = '_NET_WM_WINDOW_TYPE_DIALOG' in tok \
                            or '_NET_WM_STATE_MODAL' in tok
            return is_dialog

    def find_visible_windows(windows_on_ws: List) -> List:
        """ Find windows visible on the screen now.

        Args:
            windows_on_ws: windows list which going to be filtered with this
                        function.
        """
        visible_windows = []
        for w in windows_on_ws:
            with NegEWMH.window_obj(NegEWMH.disp, w.window) as win:
                xprop = NegEWMH.ewmh.getWmState(win, str=True)
                if '_NET_WM_STATE_HIDDEN' not in xprop:
                    visible_windows.append(w)

        return visible_windows

