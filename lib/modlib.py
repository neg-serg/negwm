import os
import sys
import traceback
import subprocess
import re
from gevent.queue import Queue
from gevent import Greenlet
from threading import Thread
from singleton import Singleton


def notify_msg(s, prefix=">>"):
    notify_msg = ['notify-send', prefix, s]
    subprocess.run(notify_msg)


def get_screen_resolution():
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
    def find_classed(self, wlist, pattern):
        return [c for c in wlist
                if c.window_class and re.search(pattern, c.window_class)]

    def find_instanced(self, wlist, pattern):
        return [c for c in wlist
                if c.window_instance and re.search(pattern, c.window_instance)]

    def find_by_role(self, wlist, pattern):
        return [c for c in wlist
                if c.window_role and re.search(pattern, c.window_role)]

    def find_named(self, wlist, pattern):
        return [c for c in wlist
                if c.name and re.search(pattern, c.name)]

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
    __metaclass__ = Singleton

    def __init__(self):
        self.daemons = {}
        self.Q = {
            sys.intern('circle'): Queue(),
            sys.intern('ns'): Queue(),
            sys.intern('flast'): Queue(),
            sys.intern('menu'): Queue(),
            sys.intern('fsdpms'): Queue(),
            sys.intern('info'): Queue(),
            sys.intern('wm3'): Queue(),
            sys.intern('vol'): Queue(),
        }

    def add_daemon(self, name):
        d = daemon_i3()
        if d not in self.daemons.keys():
            self.daemons[name] = d
            self.daemons[name].bind_fifo(name)

    def mainloop(self, mods):
        def loop(name):
            while True:
                self.Q[name].put_nowait(
                    self.daemons[name].fifo_listner(
                        self.mods[name], name
                    )
                )
                Greenlet.spawn(self.worker)

        self.mods = mods
        for name in self.Q:
            print(f"[STARTING {name}]")
            Thread(target=loop, args=(name, ), daemon=True).start()
            print(f"[OK {name}]")

    def worker(self, name):
        while not self.Q[name].empty():
            self.Q[name].get()

class daemon_i3():
    __metaclass__ = Singleton

    def __init__(self):
        self.fifos = {}

    def bind_fifo(self, name):
        self.fifos[name] = \
            os.path.realpath(os.path.expandvars('$HOME/tmp/' + name + '.fifo'))
        if os.path.exists(self.fifos[name]):
            os.remove(self.fifos[name])
        try:
            os.mkfifo(self.fifos[name])
        except OSError as oe:
            if oe.errno != os.errno.EEXIST:
                raise

    def fifo_listner(self, mod, name):
        with open(self.fifos[name]) as fifo:
            while True:
                data = fifo.read()
                if not len(data):
                    break
                eval_str = data.split('\n', 1)[0]
                args = list(filter(lambda x: x != '', eval_str.split(' ')))
                try:
                    mod.switch(args)
                except TypeError:
                    print(traceback.format_exc())

