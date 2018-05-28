#!/usr/bin/python3

import subprocess
import shlex
from os.path import expanduser
from modi3cfg import modi3cfg
from singleton import Singleton


class env():
    def __init__(self, name, cfg):
        self.name = name
        self.sockpath = expanduser(
            f'~/1st_level/{name}.socket'
        )
        self.window_class = cfg.get(name, {}).get("window_class", {})

        # get terminal from config, use Alacritty by default
        self.term = cfg.get(name, {}).get("term", "alacritty").lower()

        self.font = cfg.get("default_font", "")
        if not self.font:
            self.font = cfg.get(name, {}).get("font", "Iosevka Term")
        self.font_size = cfg.get("default_font_size", "")
        if not self.font_size:
            self.font_size = cfg.get(name, {}).get("font_size", "18")

        self.tmux_session_attach = \
            f"tmux -S {self.sockpath} a -t {name}"
        self.tmux_new_session = \
            f"tmux -S {self.sockpath} new-session -s {name}"
        self.term_params = {
            "alacritty": ["alacritty"] + [
                "-t", self.window_class,
                "-e", "dash", "-c"
            ],
            "alacritty-ncmpcpp": [
                "alacritty",
                "--config-file",
                expanduser("~/.config/alacritty/ncmpcpp.yml")
            ] + [
                "-t", self.window_class,
                "-e", "dash", "-c"
            ],
            "st": ["st"] + [
                "-c", self.window_class,
                "-f", self.font + ":size=" + str(self.font_size),
                "-e", "dash", "-c",
            ],
            "urxvt": ["urxvt"] + [
                "-name", self.window_class,
                "-fn", "xft:" + self.font + ":size=" + str(self.font_size),
                "-e", "dash", "-c",
            ],
            "xterm": ["xterm"] + [
                '-class', self.window_class,
                '-fa', "xft:" + self.font + ":size=" + str(self.font_size),
                "-e", "dash", "-c",
            ],
            "cool-retro-term": ["cool-retro-term"] + [
                "-e", "dash", "-c",
            ],
        }

        colorscheme = cfg.get("colorscheme", "")
        if not colorscheme:
            colorscheme = cfg.get(name, {}).get("colorscheme", 'dark3')
        self.set_colorscheme = \
            f"{expanduser('~/bin/dynamic-colors')} switch {colorscheme};"
        self.postfix = cfg.get(name, {}).get("postfix", '')
        if self.postfix and self.postfix[0] != '-':
            self.postfix = '\\; ' + self.postfix
        self.tmuxed = int(cfg.get(name, {}).get("tmuxed", 1))
        if not self.tmuxed:
            self.prog = cfg.get(name, {}).get('prog', 'true')


class tm(modi3cfg):
    __metaclass__ = Singleton

    def __init__(self, i3, loop=None):
        modi3cfg.__init__(self, i3, convert_me=False)
        self.envs = {}
        for app in self.cfg:
            self.envs[app] = env(app, self.cfg)

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
            "run": self.run,
            "reload": self.reload_config,
        }[args[0]](*args[1:])

    def detect_session_bind(self):
        session_list = subprocess.run(
            shlex.split(f"tmux -S {self.env.sockpath} list-sessions"),
            stdout=subprocess.PIPE
        ).stdout
        return subprocess.run(
            shlex.split(
                f"awk -F ':' '/{self.env.name}/ {{print $1}}'"
            ),
            stdout=subprocess.PIPE,
            input=(session_list)
        ).stdout.decode()

    def attach_to_session(self):
        self.run_app(
            self.env.term_params[self.env.term] +
            [f"{self.env.set_colorscheme} {self.env.tmux_session_attach}"]
        )

    def search_classname(self):
        return subprocess.run(
            shlex.split(f"xdotool search --classname {self.env.window_class}"),
            stdout=subprocess.PIPE
        ).stdout

    def create_new_session(self):
        self.run_app(
            self.env.term_params[self.env.term] +
            [f"{self.env.set_colorscheme} {self.env.tmux_new_session} {self.env.postfix} && \
                {self.env.tmux_session_attach}"]
        )

    def run(self, name):
        self.env = self.envs[name]
        if self.env.tmuxed:
            if self.env.name in self.detect_session_bind():
                wid = self.search_classname()
                try:
                    if int(wid.decode()):
                        pass
                except ValueError:
                    self.attach_to_session()
            else:
                self.create_new_session()
        else:
            self.run_app(
                self.env.term_params[self.env.term] + [
                    self.env.set_colorscheme + self.env.prog
                ]
            )

