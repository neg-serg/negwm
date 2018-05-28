#!/usr/bin/pypy3

import subprocess
import shlex
import re
from os.path import expanduser
from modi3cfg import modi3cfg
from singleton import Singleton


class tm(modi3cfg):
    __metaclass__ = Singleton

    def __init__(self, i3, loop=None):
        self.session_name = 'main'
        self.socket_path = expanduser(
            f'~/1st_level/{self.session_name}.socket'
        )
        self.term_name = "MainTerminal"
        self.prefix = f"{expanduser('~/bin/dynamic-colors')} switch dark3;"
        self.tmux_session_attach = \
            f"tmux -S {self.socket_path} a -t {self.session_name}"
        self.tmux_new_session = \
            f"tmux -S {self.socket_path} new-session -s {self.session_name}"

        self.params = {
            "alacritty": ["alacritty"] + [
                "-t", self.term_name,
                "-e", "dash", "-c"
            ]
        }

    def run_app(self, args):
        subprocess.Popen(args)

    def switch(self, args):
        """ Defines pipe-based IPC for cirled module. With appropriate
            function bindings.

            This function defines bindings to the named_scratchpad methods that
            can be used by external users as i3-bindings, sxhkd, etc. Need the
            [send] binary which can send commands to the appropriate FIFO.

            Args:
                args (List): argument list for the selected function.
        """
        {
            "term": self.run,
        }[args[0]](*args[1:])

    def detect_session_bind(self):
        session_list = subprocess.run(
            shlex.split(f"tmux -S {self.socket_path} list-sessions"),
            stdout=subprocess.PIPE
        ).stdout
        return subprocess.run(
            shlex.split(f"awk -F ':' '/{self.session_name}/ {{print $1}}'"),
            stdout=subprocess.PIPE,
            input=(session_list)
        ).stdout.decode()

    def attach_to_session(self):
        self.run_app(
            self.params["alacritty"] +
            [f"{self.prefix} {self.tmux_session_attach}"]
        )

    def search_classname(self):
        return subprocess.run(
            shlex.split(f"xdotool search --classname {self.term_name}"),
            stdout=subprocess.PIPE
        ).stdout

    def create_new_session(self):
        self.run_app(
            self.params["alacritty"] +
            [f"{self.prefix} {self.tmux_new_session} && \
                {self.tmux_session_attach}"]
        )

    def run(self):
        if self.session_name in self.detect_session_bind():
            wid = self.search_classname()
            try:
                if int(wid.decode()):
                    pass
            except ValueError:
                self.attach_to_session()
        else:
            self.create_new_session()


