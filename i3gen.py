import os
from threading import Thread, Lock
from collections import deque

class Singleton(object):
    __singleton_lock = Lock()
    __singleton_instance = None

    @classmethod
    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance

        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.__singleton_instance

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
