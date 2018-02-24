import os
import traceback
from threading import Thread
from collections import deque
from singleton import *

class Matcher(object):
    def match(self, win, tag):
        def match_class():
            return win.window_class in matched_list

        def match_instance():
            return win.window_instance in matched_list

        def match_class_r():
            for reg in matched_list:
                cls_by_regex=self.winlist.find_classed(reg)
                if cls_by_regex:
                    for class_regex in cls_by_regex:
                        if win.window_class == class_regex.window_class:
                            return True
            return False

        def match_instance_r():
            for reg in matched_list:
                inst_by_regex=self.winlist.find_instanced(reg)
                if inst_by_regex:
                    for inst_regex in inst_by_regex:
                        if win.window_instance == inst_regex.window_instance:
                            return True
            return False

        def match_role_r():
            for reg in matched_list:
                role_by_regex=self.winlist.find_by_role(reg)
                if role_by_regex:
                    for role_regex in role_by_regex:
                        if win.window_role == role_regex.window_role:
                            return True
            return False

        def match_name_r():
            for reg in matched_list:
                name_by_regex=self.winlist.find_named(reg)
                if name_by_regex:
                    for name_regex in name_by_regex:
                        if win.name == name_regex.name:
                            return True
            return False

        factors=[
            "class", "instance",
            "class_r", "instance_r", "name_r", "role_r"
        ]

        match={
            "class": match_class,
            "instance": match_instance,
            "class_r": match_class_r,
            "instance_r": match_instance_r,
            "role_r": match_role_r,
            "name_r": match_name_r,
        }

        for f in factors:
            matched_list=self.cfg.get(tag,{}).get(f, {})
            if match[f](): return True
        return False

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

    def fifo_listner(self, mod, name):
        with open(self.fifos[name]) as fifo:
            while True:
                data = fifo.read()
                if not len(data):
                    break
                eval_str=data.split('\n', 1)[0]
                args=list(filter(lambda x: x != '', eval_str.split(' ')))
                try:
                    mod.switch(args)
                except:
                    print(traceback.format_exc())

    def worker(self):
        while True:
            if self.d:
                raise SystemExit()
            self.d.get()

    def mainloop(self, mod, name):
        while True:
            self.d.append(self.fifo_listner(mod, name))
            Thread(target=self.worker).start()
