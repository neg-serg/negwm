#!/usr/bin/pypy3
""" i3 negi3mods daemon script
Usage:
    negi3mods.py

Created by :: Neg
email :: <serg.zorg@gmail.com>
github :: https://github.com/neg-serg?tab=repositories
year :: 2018

"""

import os
import sys
import socket
from threading import Thread, Event
import importlib
import inotify.adapters
import atexit
import subprocess
import shlex
import cgitb
from lib.modlib import daemon_manager


# Create a pid lock with abstract socket.
# Taken from [https://stackoverflow.com/questions/788411/check-to-see-if-python-script-is-running]
def get_lock(process_name):
    # Without holding a reference to our socket somewhere it gets garbage
    # collected when the function exits
    get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    try:
        get_lock._lock_socket.bind('\0' + process_name)
        print('locking successful')
    except socket.error:
        print('lock exists')
        sys.exit()


class Negi3Mods():
    def __init__(self):
        self.i3_mod_event = Event()
        self.i3_config_event = Event()
        self.mods = {
            'circle': {},
            'ns': {},
            'flast': {},
            'menu': {},
            'fsdpms': {},
            'info': {},
            'wm3': {},
            'vol': {},
        }
        if "menu" in self.mods:
            self.mods["menu"]["no_i3"] = True
        user_name = os.environ.get("USER", "neg")
        xdg_config_path = os.environ.get(
            "XDG_CONFIG_HOME", "/home/" + user_name + "/.config/"
        )
        self.i3_path = xdg_config_path+"/i3/"

    def watch(self, watch_dir, file_path,
              ev, watched_inotify_event="IN_MODIFY",
              stackless=True):
        if stackless:
            watch_dir = watch_dir
        else:
            watch_dir = watch_dir.encode()
        i = inotify.adapters.Inotify()
        i.add_watch(watch_dir)

        try:
            for event in i.event_gen():
                if event is not None:
                    (header, type_names, watch_path, filename) = event
                    if stackless:
                        if filename == file_path and watched_inotify_event in type_names:
                            ev.set()
                    else:
                        if filename.decode() == file_path and watched_inotify_event in type_names:
                            ev.set()
        finally:
            i.remove_watch(watch_dir)

    def i3_module_inotify(self):
        for mod in self.mods.keys():
            Thread(
                target=self.watch,
                args=(self.i3_path + "/cfg/", mod + '.cfg', self.i3_mod_event),
                daemon=True
            ).start()

    def i3_config_inotify(self):
        Thread(
            target=self.watch,
            args=(self.i3_path, '_config', self.i3_config_event),
            daemon=True
        ).start()

    def dump_configs(self):
        import toml
        try:
            for mod in self.mods.keys():
                m = self.mods[mod]
                with open(self.i3_path + "/cfg/" + mod + ".cfg", "w") as fp:
                    toml.dump(m["instance"].cfg, fp)
        except:
            pass

    def load_modules(self):
        for mod in self.mods.keys():
            m = self.mods[mod]
            i3mod = importlib.import_module(mod + "d")
            m["instance"] = getattr(i3mod, mod)()
            m["manager"] = daemon_manager()
            m["manager"].add_daemon(mod)
            Thread(
                target=m["manager"].daemons[mod].mainloop,
                args=(m["instance"], mod,),
                daemon=True
            ).start()
            if mod == "info":
                Thread(target=m["instance"].listen, daemon=True).start()
            print(f'loaded {m["instance"]}')

    def return_to_i3main(self):
        # you should bypass method itself, no return value
        for mod in self.mods:
            if not self.mods.get(mod, {}).get("no_i3", {}):
                Thread(
                    target=self.mods[mod]["instance"].i3.main,
                    daemon=False
                ).start()

    def cleanup_on_exit(self):
        def cleanup_everything():
            for mod in self.mods.keys():
                fifo = self.mods[mod]["manager"].daemons[mod].fifos[mod]
                if os.path.exists(fifo):
                    os.remove(fifo)
        atexit.register(cleanup_everything)

    def i3_config_reload_thread(self):
        def reload_thread_payload():
            while True:
                if self.i3_config_event.wait():
                    self.i3_config_event.clear()
                    with open(self.i3_path + "/config", "w") as fp:
                        p = subprocess.Popen(
                            shlex.split("ppi3 " + self.i3_path + "_config"),
                            stdout=fp
                        )
                        (output, err) = p.communicate()
                        p.wait()
                    check_config = subprocess.run(
                        ['i3', '-C'],
                        stdout=subprocess.PIPE
                    ).stdout.decode('utf-8')
                    if len(check_config):
                        subprocess.Popen(
                            shlex.split(
                                f"notify-send '{check_config.encode('utf-8')}'"
                            )
                        )
                    check_config = ""
        Thread(target=reload_thread_payload, daemon=True).start()

    def i3_module_reload_thread(self):
        def reload_thread_payload():
            while True:
                if self.i3_mod_event.wait():
                    self.i3_mod_event.clear()
                    for mod in self.mods.keys():
                        subprocess.Popen(
                            shlex.split(
                                self.i3_path + "send " + mod + " reload"
                            )
                        )
        Thread(target=reload_thread_payload, daemon=True).start()

    def main(self):
        self.cleanup_on_exit()
        self.load_modules()
        self.i3_module_inotify()
        self.i3_module_reload_thread()
        self.i3_config_inotify()
        self.i3_config_reload_thread()
        print("[modules loaded]")
        self.return_to_i3main()


if __name__ == '__main__':
    get_lock('negi3mods.py')
    cgitb.enable(format='text')
    daemon = Negi3Mods()
    daemon.main()

