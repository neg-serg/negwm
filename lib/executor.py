""" Tmux Manager.

Give simple and consistent way for user to create tmux sessions on dedicated
sockets. Also it can run simply run applications without Tmux. The main
advantage is dynamic config reloading and simplicity of adding or modifing of
various parameters, also it works is faster then dedicated scripts, because
there is no parsing / translation phase here in runtime.
"""
import subprocess
import os
import errno
import shlex
import shutil
import threading
import multiprocessing
import yaml
import yamlloader

from typing import List
from os.path import expanduser
from cfg import cfg
from singleton import Singleton
from misc import Misc


class env():
    """ Environment class. It is a helper for tmux manager to store info about
        currently selected application. This class rules over parameters and
        settings of application, like used terminal enumator, fonts, all path
        settings, etc.
    Parents:
        config: configuration manager to autosave/autoload
                TOML-configutation with inotify

    Metaclass:
        Use Singleton metaclass from singleton module.

    """
    def __init__(self, name: str, config: dict) -> None:
        self.name = name
        self.tmux_socket_dir = expanduser('/dev/shm/tmux_sockets')
        self.alacritty_cfg_dir = expanduser('/dev/shm/alacritty_cfg')
        self.sockpath = expanduser(f'{self.tmux_socket_dir}/{name}.socket')
        self.default_alacritty_cfg_path = "~/.config/alacritty/alacritty.yml"
        Misc.create_dir(self.tmux_socket_dir)
        Misc.create_dir(self.alacritty_cfg_dir)
        try:
            os.makedirs(self.tmux_socket_dir)
        except OSError as dir_not_created:
            if dir_not_created.errno != errno.EEXIST:
                raise

        try:
            os.makedirs(self.alacritty_cfg_dir)
        except OSError as dir_not_created:
            if dir_not_created.errno != errno.EEXIST:
                raise

        self.window_class = config.get(name, {}).get("window_class", {})

        # get terminal from config, use Alacritty by default
        self.term = config.get(name, {}).get("term", "alacritty").lower()

        self.font = config.get("default_font", "")
        if not self.font:
            self.font = config.get(name, {}).get("font", "Iosevka Term")
        self.font_size = config.get("default_font_size", "")
        if not self.font_size:
            self.font_size = config.get(name, {}).get("font_size", "18")

        self.tmux_session_attach = \
            f"tmux -S {self.sockpath} a -t {name}"
        self.tmux_new_session = \
            f"tmux -S {self.sockpath} new-session -s {name}"
        colorscheme = config.get("colorscheme", "")
        if not colorscheme:
            colorscheme = config.get(name, {}).get("colorscheme", 'dark3')
        self.set_colorscheme = \
            f"{expanduser('~/bin/dynamic-colors')} switch {colorscheme};"
        self.postfix = config.get(name, {}).get("postfix", '')
        if self.postfix and self.postfix[0] != '-':
            self.postfix = '\\; ' + self.postfix
        self.tmuxed = int(config.get(name, {}).get("tmuxed", 1))
        if not self.tmuxed:
            prog_to_dtach = config.get(name, {}).get('prog_detach', '')
            if prog_to_dtach:
                self.prog = \
                    f'dtach -A ~/1st_level/{name}.session {prog_to_dtach}'
            else:
                self.prog = config.get(name, {}).get('prog', 'true')
        self.set_wm_class = config.get(name, {}).get('set_wm_class', '')
        self.set_instance = config.get(name, {}).get('set_instance', '')

        self.x_pad = config.get(name, {}).get('x_padding', '2')
        self.y_pad = config.get(name, {}).get('y_padding', '2')

        self.create_term_params(config, name)

        def join_processes():
            for prc in multiprocessing.active_children():
                prc.join()

        threading.Thread(target=join_processes, args=(), daemon=True).start()

    @staticmethod
    def generate_alacritty_config(
            alacritty_cfg_dir, config: dict, name: str) -> str:
        """ Config generator for alacritty.
            We need it because of alacritty cannot bypass most of user
            parameters with command line now.

            Args:
                alacritty_cfg_dir: alacritty config dir
                config: config dirtionary
                name(str): name of config to generate

            Return:
               cfgname(str): configname
        """
        alacritty_suffix = config.get(name, {}).get('alacritty_suffix', {})
        if not alacritty_suffix:
            alacritty_suffix = config.get(name, {}).get('window_class')

        alacritty_suffix = expanduser(alacritty_suffix + '.yml')
        cfgname = expanduser(f'{alacritty_cfg_dir}/{alacritty_suffix}')

        if not os.path.exists(cfgname):
            shutil.copyfile(
                expanduser("~/.config/alacritty/alacritty.yml"),
                cfgname
            )
        return cfgname

    def yaml_config_create(self, custom_config: str) -> None:
        """ Create config for alacritty

            Args:
                custom_config(str): config name to create
        """
        with open(custom_config, "r") as cfg_file:
            try:
                conf = yaml.load(
                    cfg_file, Loader=yamlloader.ordereddict.CSafeLoader)
                if conf is not None:
                    conf["font"]["normal"]["family"] = self.font
                    conf["font"]["bold"]["family"] = self.font
                    conf["font"]["italic"]["family"] = self.font
                    conf["font"]["size"] = self.font_size
                    conf["window"]["padding"]['x'] = int(self.x_pad)
                    conf["window"]["padding"]['y'] = int(self.y_pad)
            except yaml.YAMLError as yamlerror:
                print(yamlerror)

        with open(custom_config, 'w', encoding='utf8') as outfile:
            try:
                yaml.dump(
                    conf,
                    outfile,
                    default_flow_style=False,
                    allow_unicode=True,
                    canonical=False,
                    explicit_start=True,
                    Dumper=yamlloader.ordereddict.CDumper
                )
            except yaml.YAMLError as yamlerror:
                print(yamlerror)

    def create_term_params(self, config: dict, name: str) -> None:
        """ This function fill self.term_opts for settings.abs

            Args:
                config(dict): config dictionary which should be adopted to
                commandline options or settings.
        """
        terminal = config.get(name, {}).get("term")
        if terminal == "alacritty":
            self.term_opts = ["alacritty"] + [
                "-t", self.window_class,
                "-e", "dash", "-c"
            ]
        elif terminal == "alacritty-custom":
            custom_config = self.generate_alacritty_config(
                self.alacritty_cfg_dir, config, name
            )
            multiprocessing.Process(
                target=self.yaml_config_create, args=(custom_config,),
                daemon=True
            ).start()
            self.term_opts = [
                "alacritty", "--live-config-reload", "--config-file",
                expanduser(custom_config)
            ] + [
                "--class", self.window_class,
                "-e", "dash", "-c"
            ]
        elif terminal == "alacritty-custom-silent":
            custom_config = self.generate_alacritty_config(
                self.alacritty_cfg_dir, config, name
            )
            multiprocessing.Process(
                target=self.yaml_config_create, args=(custom_config,),
                daemon=True
            ).start()
            self.term_opts = [
                "alacritty", '-qq', "--live-config-reload", "--config-file",
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


class executor(cfg):
    """ Tmux Manager class. Easy and consistent way to create tmux sessions on
        dedicated sockets. Also it can run simply run applications without
        Tmux. The main advantage is dynamic config reloading and simplicity of
        adding or modifing of various parameters.

    Parents:
        cfg: configuration manager to autosave/autoload
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
        cfg.__init__(self, i3, convert_me=False)
        self.envs = {}
        for app in self.cfg:
            self.envs[app] = env(app, self.cfg)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        for envi in self.envs:
            del envi

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

    def send_msg(self, args: List) -> None:
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

    @staticmethod
    def detect_session_bind(sockpath, name) -> str:
        """ Find target session for given socket.
        """
        session_list = subprocess.run(
            shlex.split(f"tmux -S {sockpath} list-sessions"),
            stdout=subprocess.PIPE
        ).stdout
        return subprocess.run(
            shlex.split(f"awk -F ':' '/{name}/ {{print $1}}'"),
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
            if self.env.name in self.detect_session_bind(
                    self.env.sockpath, self.env.name):
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

