""" Module contains routines used by several another modules.

There are several superclasses and generic modules here.
The main reason is "don't repeat yourself", DRY.

Matcher:
    Matcher: class to check that window can be tagged with given tag by
    WM_CLASS, WM_INSTANCE, regexes, etc. It can be used by named scrachpad,
    circle run-or-raise, etc.

Daemon manager and mod daemon:
    Mod daemon creates appropriate files in the /dev/shm directory.

    Daemon manager handles all requests to this named pipe based API with help
    of asyncio.

"""

import os
import sys
import subprocess
from contextlib import contextmanager
import traceback
import re
import errno
import asyncio
import aiofiles

import Xlib
from Xlib import display
from Xlib.ext import randr
import Xlib.display
from ewmh import EWMH

from typing import List, Iterator
from singleton import Singleton


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


class Misc():
    @staticmethod
    def print_traceback() -> None:
        print(traceback.format_exc())

    @staticmethod
    def create_dir(dirname):
        try:
            os.makedirs(dirname)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    @staticmethod
    def i3path() -> str:
        """ Easy way to return i3 config path. May be improved.
        """
        xdg_config_path = os.environ.get("XDG_CONFIG_HOME")
        i3_path = xdg_config_path + "/i3/"
        return i3_path

    @staticmethod
    def extract_xrdb_value(field: str) -> str:
        """ Extracts field from xrdb executable.
        """
        out = subprocess.run(
            f"xrdb -query | rg '{field}' | awk '{{print $2}}'",
            shell=True,
            stdout=subprocess.PIPE
        ).stdout
        if out is not None and out:
            ret = out.decode('UTF-8').split()[0]
            return ret

    @classmethod
    def notify_msg(cls, msg: str, prefix: str = " "):
        """ Send messages via notify-osd based notifications.

            Args:
                msg: message string.
                prefix: optional prefix for message string.
        """
        foreground_color = cls.extract_xrdb_value('\\*.foreground')
        notify_msg = [
            'notify-send',
            f"<span weight='normal' color='{foreground_color}'>" +
            prefix + msg +
            "</span>"
        ]
        subprocess.run(notify_msg)


class Negi3ModsDisplay():
    d = display.Display()
    s = d.screen()
    window = s.root.create_window(0, 0, 1, 1, 1, s.root_depth)
    xrandr_cache = randr.get_screen_info(window)._data
    resolution_list = []

    @classmethod
    def get_screen_resolution(cls) -> dict:
        size_id = cls.xrandr_cache['size_id']
        resolution = cls.xrandr_cache['sizes'][size_id]
        return {
            'width': int(resolution['width_in_pixels']),
            'height': int(resolution['height_in_pixels'])
        }

    @classmethod
    def get_screen_resolution_data(cls) -> dict:
        return cls.xrandr_cache['sizes']

    @classmethod
    def xrandr_resolution_list(cls) -> dict:
        if not cls.resolution_list:
            delimiter = 'x'
            resolution_data = cls.get_screen_resolution_data()
            for size_id, res in enumerate(resolution_data):
                if res is not None and res:
                    cls.resolution_list += [(
                        str(size_id) + ': ' +
                        str(res['width_in_pixels']) +
                        delimiter +
                        str(res['height_in_pixels'])
                    )]

        return cls.resolution_list

    @classmethod
    def set_screen_size(cls, size_id=0) -> None:
        subprocess.run(['xrandr', '-s', str(size_id)])


class Matcher(object):
    """ Generic matcher class

    Used by several classes. It can match windows by several criteria, which
    I am calling "factor", including:
        - by class, by class regex
        - by instance, by instance regex
        - by role, by role regex
        - by name regex

    Of course this list can by expanded. It uses sys.intern hack for better
    performance and simple caching. One of the most resource intensive part of
    negi3mods.

    """
    def find_classed(self, wlist: List, pattern: str) -> Iterator:
        return (c for c in wlist
                if c.window_class and re.search(pattern, c.window_class))

    def find_instanced(self, wlist: List, pattern: str) -> Iterator:
        return (c for c in wlist
                if c.window_instance and re.search(pattern, c.window_instance))

    def find_by_role(self, wlist: List, pattern: str) -> Iterator:
        return (c for c in wlist
                if c.window_role and re.search(pattern, c.window_role))

    def find_named(self, wlist: List, pattern: str) -> Iterator:
        return (c for c in wlist
                if c.name and re.search(pattern, c.name))

    def class_r(self) -> bool:
        for pattern in self.matched_list:
            cls_by_regex = self.find_classed(
                self.winlist.leaves(),
                pattern
            )
            if cls_by_regex:
                for class_regex in cls_by_regex:
                    if self.win.window_class == class_regex.window_class:
                        return True
        return False

    def instance_r(self) -> bool:
        for pattern in self.matched_list:
            inst_by_regex = self.find_instanced(
                self.winlist.leaves(),
                pattern
            )
            if inst_by_regex:
                for inst_regex in inst_by_regex:
                    if self.win.window_instance == inst_regex.window_instance:
                        return True
        return False

    def role_r(self) -> bool:
        for pattern in self.matched_list:
            role_by_regex = self.find_by_role(
                self.winlist.leaves(),
                pattern
            )
            if role_by_regex:
                for role_regex in role_by_regex:
                    if self.win.window_role == role_regex.window_role:
                        return True
        return False

    def name_r(self) -> bool:
        for pattern in self.matched_list:
            name_by_regex = self.find_named(
                self.winlist.leaves(),
                pattern
            )
            if name_by_regex:
                for name_regex in name_by_regex:
                    if self.win.name == name_regex.name:
                        return True
        return False

    def match_all(self) -> bool:
        return len(self.matched_list) > 0

    def match(self, win, tag: str) -> bool:
        self.win = win
        factors = [
            sys.intern("class"),
            sys.intern("instance"),
            sys.intern("role"),
            sys.intern("class_r"),
            sys.intern("instance_r"),
            sys.intern("name_r"),
            sys.intern("role_r"),
            sys.intern('match_all')
        ]

        match = {
            sys.intern("class"): lambda: win.window_class in self.matched_list,
            sys.intern("instance"): lambda: win.window_instance in self.matched_list,
            sys.intern("role"): lambda: win.window_role in self.matched_list,
            sys.intern("class_r"): self.class_r,
            sys.intern("instance_r"): self.instance_r,
            sys.intern("role_r"): self.role_r,
            sys.intern("name_r"): self.name_r,
            sys.intern("match_all"): self.match_all,
        }

        for f in factors:
            self.matched_list = self.cfg.get(tag, {}).get(f, {})
            if self.matched_list is not None and self.matched_list != []:
                if match[f]():
                    return True
            else:
                print(f'error for ftor={f} and match_list={self.matched_list}')
        return False


class daemon_manager():
    """ Daemon manager. Rules by negi3mods, dispatch messages.

        Every module has indivisual main loop with indivisual neg-ipc-file.

    Metaclass:
        Use Singleton metaclass from singleton module.
    """
    __metaclass__ = Singleton

    def __init__(self, mods: List) -> None:
        self.files = {}  # file list
        self.mods = mods  # mods list

    async def ipc_listner(self, name: str) -> None:
        """ Async neg-ipc-file listner

            Args:
                name(str): module name.
        """
        while True:
            async with aiofiles.open(self.files[name], mode='r') as fd:
                while True:
                    data = await fd.read()
                    if not len(data):
                        break
                    eval_str = data.split('\n', 1)[0]
                    args = list(filter(lambda x: x != '', eval_str.split(' ')))
                    try:
                        self.mods[name].switch(args)
                    except Exception:
                        Misc.print_traceback()

    def add_ipc(self, name: str) -> None:
        """ Add negi3mods IPC.
        """
        self.files[name] = self.create_ipc(name)

    @staticmethod
    def create_ipc(name: str) -> str:
        """ Create IPC for the given name
        """
        neg_ipc_file = os.path.realpath(os.path.expandvars(
            '/dev/shm/' + name + '.nif'))
        if os.path.exists(neg_ipc_file):
            os.remove(neg_ipc_file)
        try:
            os.mkfifo(neg_ipc_file)
        except OSError as oe:
            if oe.errno != os.errno.EEXIST:
                raise
        finally:
            return neg_ipc_file

    def mainloop(self, loop) -> None:
        """ Mainloop for module. Started by negi3mods in separated thread.

            Args:
                loop: asyncio.loop should be bypassed to function if you are
                using new thread.
        """
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            asyncio.wait([self.ipc_listner(m) for m in self.mods])
        )

