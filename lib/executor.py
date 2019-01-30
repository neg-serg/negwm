""" Tmux Manager.

Give simple and consistent way for user to create tmux sessions on dedicated
sockets. Also it can run simply run applications without Tmux. The main
advantage is dynamic config reloading and simplicity of adding or modifing of
various parameters, also it works is faster then dedicated scripts, because
there is no parsing / translation phase here in runtime.
"""
import subprocess
import os
import shlex
import shutil
import yaml
from typing import List
from os.path import expanduser
from modi3cfg import modi3cfg
from singleton import Singleton
from multiprocessing import Process


class env():
    """ Environment class. It is a helper for tmux manager to store info about
        currently selected application. This class rules over parameters and
        settings of application, like used terminal enumator, fonts, all path
        settings, etc.
    Parents:
        modi3cfg: configuration manager to autosave/autoload
                  TOML-configutation with inotify

    Metaclass:
        Use Singleton metaclass from singleton module.

    """
    def __init__(self, name: str, cfg: dict) -> None:
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
            prog_to_dtach = cfg.get(name, {}).get('prog_detach', '')
            if prog_to_dtach:
                self.prog = \
                    f'dtach -A ~/1st_level/{name}.session {prog_to_dtach}'
            else:
                self.prog = cfg.get(name, {}).get('prog', 'true')
        self.set_wm_class = cfg.get(name, {}).get('set_wm_class', '')
        self.set_instance = cfg.get(name, {}).get('set_instance', '')

        self.x_pad = cfg.get(name, {}).get('x_padding', '2')
        self.y_pad = cfg.get(name, {}).get('y_padding', '2')

        self.create_term_params(cfg, name)

    def generate_alacritty_config(self, cfg: dict, name: str) -> None:
        alacritty_suffix = cfg.get(name, {}).get('alacritty_suffix', {})
        if not alacritty_suffix:
            alacritty_suffix = cfg.get(name, {}).get('window_class')

        ret = expanduser("~/.config/alacritty/alacritty.yml")

        alacritty_suffix = expanduser(
            "alacritty_" + alacritty_suffix + '.yml'
        )
        cfgname = expanduser("~/tmp/" + alacritty_suffix)
        if not os.path.exists(cfgname):
            shutil.copyfile(
                expanduser("~/.config/alacritty/alacritty.yml"),
                cfgname
            )
        ret = cfgname
        return ret

    def fileprocess(self, custom_config: str) -> None:
        with open(custom_config, "r") as fp:
            try:
                conf = yaml.load(fp)
                conf["font"]["normal"]["family"] = self.font
                conf["font"]["bold"]["family"] = self.font
                conf["font"]["italic"]["family"] = self.font
                conf["font"]["size"] = self.font_size
                conf["window"]["padding"]['x'] = self.x_pad
                conf["window"]["padding"]['y'] = self.y_pad
            except yaml.YAMLError as e:
                print(e)

        with open(custom_config, 'w', encoding='utf8') as outfile:
            try:
                yaml.dump(
                    conf,
                    outfile,
                    default_flow_style=False,
                    allow_unicode=True,
                    canonical=False,
                    explicit_start=True
                )
            except yaml.YAMLError as e:
                print(e)

    def create_term_params(self, cfg: dict, name: str) -> None:
        terminal = cfg.get(name, {}).get("term")
        if terminal == "alacritty":
            self.term_opts = ["alacritty"] + [
                "-t", self.window_class,
                "-e", "dash", "-c"
            ]
        elif terminal == "alacritty-custom":
            custom_config = self.generate_alacritty_config(cfg, name)
            Process(
                target=self.fileprocess, args=(custom_config,), daemon=True
            ).start()
            self.term_opts = [
                "alacritty", "--live-config-reload", "--config-file",
                expanduser(custom_config)
            ] + [
                "--class", self.window_class,
                "-e", "dash", "-c"
            ]
        elif terminal == "st":
            self.term_opts = ["st"] + [
                "-c", self.window_class,
                "-f", self.font + ":size=" + str(self.font_size),
                "-e", "dash", "-c",
            ]
        elif terminal == "urxvt":
            self.term_opts = ["urxvt"] + [
                "-name", self.window_class,
                "-fn", "xft:" + self.font + ":size=" + str(self.font_size),
                "-e", "dash", "-c",
            ]
        elif terminal == "xterm":
            self.term_opts = ["xterm"] + [
                '-class', self.window_class,
                '-fa', "xft:" + self.font + ":size=" + str(self.font_size),
                "-e", "dash", "-c",
            ]
        elif terminal == "cool-retro-term":
            self.term_opts = ["cool-retro-term"] + [
                "-e", "dash", "-c",
            ]


class executor(modi3cfg):
    """ Tmux Manager class. Easy and consistent way to create tmux sessions on
        dedicated sockets. Also it can run simply run applications without
        Tmux. The main advantage is dynamic config reloading and simplicity of
        adding or modifing of various parameters.

    Parents:
        modi3cfg: configuration manager to autosave/autoload
                  TOML-configutation with inotify

    Metaclass:
        Use Singleton metaclass from singleton module.

    """
    __metaclass__ = Singleton

    def __init__(self, i3, loop=None) -> None:
        """ Init function.

        Arguments for this constructor used only for compatibility.

        Args:
            i3: i3ipc connection(not used).
            loop: asyncio loop. It's need to be given as parameter because of
                  you need to bypass asyncio-loop to the thread(not used).
        """
        modi3cfg.__init__(self, i3, convert_me=False)
        self.envs = {}
        for app in self.cfg:
            self.envs[app] = env(app, self.cfg)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        for env in self.envs:
            del env

    def run_app(self, args: List) -> None:
        """ Wrapper to run selected application in background.
            Args:
                args (List): arguments list.
        """
        if not self.env.set_wm_class:
            subprocess.Popen(args)
        else:
            if not self.env.set_instance:
                self.env.set_instance = self.env.set_wm_class
            subprocess.Popen(
                [
                    './wm_class',
                    '--run',
                    self.env.set_wm_class,
                    self.env.set_instance,
                ] + args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def switch(self, args: List) -> None:
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

    def detect_session_bind(self) -> str:
        """ Find target session for given socket.
        """
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

    def attach_to_session(self) -> None:
        """ Run tmux to attach to given socket.
        """
        self.run_app(
            self.env.term_opts +
            [f"{self.env.set_colorscheme} {self.env.tmux_session_attach}"]
        )

    def search_classname(self) -> str:
        """ Search for selected window class.
        """
        return subprocess.run(
            shlex.split(f"xdotool search --classname {self.env.window_class}"),
            stdout=subprocess.PIPE
        ).stdout

    def create_new_session(self) -> None:
        """ Run tmux to create the new session on given socket.
        """
        self.run_app(
            self.env.term_opts +
            [f"{self.env.set_colorscheme} \
            {self.env.tmux_new_session} {self.env.postfix} && \
                {self.env.tmux_session_attach}"]
        )

    def run(self, name: str) -> None:
        """ Entry point, run application with Tmux on dedicated socket(in most
            cases), or without tmux, if config value tmuxed=0.
            Args:
                name (str): target application name, with configuration taken
                            from TOML.
        """
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
                self.env.term_opts + [
                    self.env.set_colorscheme + self.env.prog
                ]
            )

