import os
from threading import Thread
from collections import deque
from singleton import *

class Matcher(object):
    def match(self, win, factor, tag):
        lst_by_factor=self.cfg.get(tag,{}).get(factor, {})
        if factor == "class":
            return win.window_class in lst_by_factor
        elif factor == "instance":
            return win.window_instance in lst_by_factor
        elif factor == "class_r":
            for reg in lst_by_factor:
                cls_by_regex=self.winlist.find_classed(reg)
                if cls_by_regex:
                    for class_regex in cls_by_regex:
                        if win.window_class == class_regex.window_class:
                            return True
        elif factor == "instance_r":
            for reg in lst_by_factor:
                inst_by_regex=self.winlist.find_instanced(reg)
                if inst_by_regex:
                    for inst_regex in inst_by_regex:
                        if win.window_instance == inst_regex.window_instance:
                            return True
        elif factor == "role_r":
            for reg in lst_by_factor:
                role_by_regex=self.winlist.find_by_role(reg)
                if role_by_regex:
                    for role_regex in role_by_regex:
                        if win.window_role == role_regex.window_role:
                            return True
        elif factor == "name_r":
            for reg in lst_by_factor:
                name_by_regex=self.winlist.find_named(reg)
                if name_by_regex:
                    for name_regex in name_by_regex:
                        if win.name == name_regex.name:
                            return True

class daemon_manager():
    __metaclass__ = Singleton
    def __init__(self):
        self.daemons={}

    def add_daemon(self, name):
        d=daemon_i3()
        if d not in self.daemons.keys():
            self.daemons[name]=d
            self.daemons[name].bind_fifo(name)

class daemon_i3():
    __metaclass__ = Singleton
    def __init__(self):
        self.d = deque()
        self.fifos={}

    def bind_fifo(self, name):
        self.fifos[name]=os.path.realpath(os.path.expandvars('$HOME/tmp/'+name+'.fifo'))
        if os.path.exists(self.fifos[name]):
            os.remove(self.fifos[name])
        try:
            os.mkfifo(self.fifos[name])
        except OSError as oe:
            if oe.errno != errno.EEXIST:
                raise

    def fifo_listner(self, singleton, name):
        with open(self.fifos[name]) as fifo:
            while True:
                data = fifo.read()
                if not len(data):
                    break
                eval_str=data.split('\n', 1)[0]
                args=list(filter(lambda x: x != '', eval_str.split(' ')))
                singleton.switch(args)

    def worker(self):
        while True:
            if self.d:
                raise SystemExit()
            self.d.get()

    def mainloop(self, singleton, name):
        while True:
            self.d.append(self.fifo_listner(singleton, name))
            Thread(target=self.worker).start()
