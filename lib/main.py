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
import traceback
import re
import errno
import asyncio
import aiofiles
from typing import List, Iterator
from singleton import Singleton


def print_traceback() -> None:
    print(traceback.format_exc())


def create_dir(dirname):
    try:
        os.makedirs(dirname)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def i3path() -> str:
    """ Easy way to return i3 config path. May be improved.
    """
    xdg_config_path = os.environ.get("XDG_CONFIG_HOME")
    i3_path = xdg_config_path + "/i3/"
    return i3_path


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


def notify_msg(msg: str, prefix: str = " "):
    """ Send messages via notify-osd based notifications.

        Args:
            msg: message string.
            prefix: optional prefix for message string.
    """
    foreground_color = extract_xrdb_value('\\*.foreground')
    notify_msg = [
        'notify-send',
        f"<span weight='normal' color='{foreground_color}'>" +
        prefix + msg +
        "</span>"
    ]
    subprocess.run(notify_msg)


def get_screen_resolution() -> dict:
    """ Return current screen resolution with help of xrandr.
    """
    out = subprocess.run(
        'xrandr | awk \'/*/{print $1}\'',
        shell=True,
        stdout=subprocess.PIPE
    ).stdout
    if out is not None and out:
        resolution = out.decode('UTF-8').split()[0].split('x')
        return {'width': int(resolution[0]), 'height': int(resolution[1])}
    else:
        return {'width': 1920, 'height': 1200}


def find_visible_windows(windows_on_ws: List) -> List:
    """ Find windows visible on the screen now.

    Unfortunately for now external xprop application used for it,
    because of i3ipc gives no information about what windows
    shown/hidden or about _NET_WM_STATE_HIDDEN attributes

    Args:
        windows_on_ws: windows list which going to be filtered with this
                       function.
    """
    visible_windows = []
    for w in windows_on_ws:
        xprop = None
        try:
            xprop = subprocess.run(
                ['xprop', '-id', str(w.window), '_NET_WM_STATE_HIDDEN'],
                stdout=subprocess.PIPE
            ).stdout
        except Exception:
            print("get some problem in [find_visible_windows] in [main]")
        if xprop is not None:
            xprop = xprop.decode('UTF-8').strip()
            if xprop == '_NET_WM_STATE_HIDDEN:  not found.':
                visible_windows.append(w)

    return visible_windows


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
        # file list
        self.files = {}

        # mods list
        self.mods = mods

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
                        print_traceback()

    def add_ipc(self, name: str) -> None:
        """ Add negi3mods IPC.
        """
        self.files[name] = self.create_ipc(name)

    def create_ipc(self, name: str) -> str:
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

