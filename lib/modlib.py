""" Module contains routines used by several another modules.

There are several superclasses and generic modules here.
The main reason is "don't repeat yourself", DRY.

Matcher:
    Matcher: class to check that window can be tagged with given tag by
    WM_CLASS, WM_INSTANCE, regexes, etc. It can be used by named scrachpad,
    circle run-or-raise, etc.

Daemon manager and mod daemon:
    Mod daemon creates appropriate fifos in the ~/tmp directory.

    Daemon manager handles all requests to this named pipe based API with help
    of asyncio.

"""

import os
import sys
import subprocess
import traceback
import re
import asyncio
import aiofiles
from gevent.queue import Queue
from singleton import Singleton


def print_traceback():
    print(traceback.format_exc())


def i3path():
    """ Easy way to return i3 config path. May be improved.
    """
    user_name = os.environ.get("USER", "neg")
    xdg_config_path = os.environ.get(
        "XDG_CONFIG_HOME", "/home/" + user_name + "/.config/"
    )
    i3_path = xdg_config_path + "/i3/"
    return i3_path


def notify_msg(msg, prefix=" "):
    """ Send messages via notify-osd based notifications.

        Args:
            msg: message string.
            prefix: optional prefix for message string.
    """
    notify_msg = [
        'notify-send',
        "<span weight='normal' color='#617287'>" +
        prefix +  msg +
        "</span>"
    ]
    subprocess.run(notify_msg)


def get_screen_resolution():
    """ Return current screen resolution with help of xrandr.
    """
    out = subprocess.run(
        'xrandr | awk \'/*/{print $1}\'',
        shell=True,
        stdout=subprocess.PIPE
    ).stdout
    if out is not None and out:
        resolution = out.decode('UTF-8').split()[0].split('x')
        ret = {'width': int(resolution[0]), 'height': int(resolution[1])}
    else:
        ret = {'width': 1920, 'height': 1200}
    return ret


def find_visible_windows(windows_on_ws):
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
                ['xprop', '-id', str(w.window)],
                stdout=subprocess.PIPE
            ).stdout
        except:
            print("get some problem in [find_visible_windows] in [modlib]")
        if xprop is not None and xprop:
            xprop = xprop.decode('UTF-8').strip()
            if '_NET_WM_STATE_HIDDEN' not in xprop:
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
    def find_classed(self, wlist, pattern):
        return (c for c in wlist
                if c.window_class and re.search(pattern, c.window_class))

    def find_instanced(self, wlist, pattern):
        return (c for c in wlist
                if c.window_instance and re.search(pattern, c.window_instance))

    def find_by_role(self, wlist, pattern):
        return (c for c in wlist
                if c.window_role and re.search(pattern, c.window_role))

    def find_named(self, wlist, pattern):
        return (c for c in wlist
                if c.name and re.search(pattern, c.name))

    def class_r(self):
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

    def instance_r(self):
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

    def role_r(self):
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

    def name_r(self):
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

    def match(self, win, tag):
        self.win = win
        factors = [
            sys.intern("class"),
            sys.intern("instance"),
            sys.intern("role"),
            sys.intern("class_r"),
            sys.intern("instance_r"),
            sys.intern("name_r"),
            sys.intern("role_r")
        ]

        match = {
            sys.intern("class"): lambda: win.window_class in self.matched_list,
            sys.intern("instance"): lambda: win.window_instance in self.matched_list,
            sys.intern("role"): lambda: win.window_role in self.matched_list,
            sys.intern("class_r"): self.class_r,
            sys.intern("instance_r"): self.instance_r,
            sys.intern("role_r"): self.role_r,
            sys.intern("name_r"): self.name_r,
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

        Every module has indivisual main loop with indivisual named-pipe(FIFO).

    Metaclass:
        Use Singleton metaclass from singleton module.
    """
    __metaclass__ = Singleton

    def __init__(self, mods):
        # FIFO list
        self.fifos = {}

        # mods list
        self.mods = mods

        # mainloop Queue dict, addressed by mod name.
        self.Q = {}
        for m in self.mods:
            self.Q[sys.intern(m)] = Queue()

    async def fifo_listner(self, name):
        """ Async FIFO(named-pipe) listner

            Args:
                name(str): module name.
        """
        while True:
            async with aiofiles.open(self.fifos[name], mode='r') as fifo:
                while True:
                    data = await fifo.read()
                    if not len(data):
                        break
                    eval_str = data.split('\n', 1)[0]
                    args = list(filter(lambda x: x != '', eval_str.split(' ')))
                    try:
                        self.mods[name].switch(args)
                    except TypeError:
                        print_traceback()

    def add_fifo(self, name):
        """ Add negi3mods FIFO.
        """
        self.fifos[name] = self.create_fifo(name)

    def create_fifo(self, name):
        """ Create FIFO for the given name
        """
        fifo = os.path.realpath(os.path.expandvars('$HOME/tmp/' + name + '.fifo'))
        if os.path.exists(fifo):
            os.remove(fifo)
        try:
            os.mkfifo(fifo)
        except OSError as oe:
            if oe.errno != os.errno.EEXIST:
                raise
        finally:
            return fifo

    def mainloop(self, loop):
        """ Mainloop for module. Started by negi3mods in separated thread.

            Args:
                loop: asyncio.loop should be bypassed to function if you are
                using new thread.
        """
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            asyncio.wait([self.fifo_listner(m) for m in self.mods])
        )

