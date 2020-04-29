""" Tmux Manager.

Give simple and consistent way for user to create tmux sessions on dedicated
sockets. Also it can run simply run applications without Tmux. The main
advantage is dynamic config reloading and simplicity of adding or modifing of
various parameters, also it works is faster then dedicated scripts, because
there is no parsing / translation phase here in runtime.
"""
import subprocess
import os
from os.path import expanduser
import shlex
import shutil
import threading
import multiprocessing
import yaml
import yamlloader
from typing import List

from extension import extension
from cfg import cfg
from misc import Misc


class env():
    """ Environment class. It is a helper for tmux manager to store info about
        currently selected application. This class rules over parameters and
        settings of application, like used terminal enumator, fonts, all path
        settings, etc.
    Parents:
        config: configuration manager to autosave/autoload
                TOML-configutation with inotify
    """

    def __init__(self, name: str, config) -> None:
        self.name = name
        cache_dir = Misc.i3path() + '/cache'
        Misc.create_dir(cache_dir)

        tmux_socket_dir = expanduser(f'{cache_dir}/tmux_sockets')
        dtach_session_dir = expanduser(f'{cache_dir}/dtach_sessions')
        self.alacritty_cfg_dir = expanduser(f'{cache_dir}/alacritty_cfg')
        self.alacritty_cfg = expanduser(os.environ.get("XDG_CONFIG_HOME") + \
            "/alacritty/alacritty.yml")

        Misc.create_dir(tmux_socket_dir)
        Misc.create_dir(self.alacritty_cfg_dir)
        Misc.create_dir(dtach_session_dir)

        self.sockpath = expanduser(f'{tmux_socket_dir}/{name}.socket')

        for sh in ['dash', 'zsh', 'bash', 'sh']:
            if shutil.which(sh):
                self.default_shell = sh
                break

        # get terminal from config, use Alacritty by default
        self.term = config.get(name, {}).get("term", "alacritty").lower()

        if os.path.exists(self.alacritty_cfg):
            if os.stat(self.alacritty_cfg).st_size == 0:
                print('Alacritty cfg {self.alacritty_cfg} is empty')
                self.term = env.terminal_fallback_detect()
        else:
            print('Alacritty cfg {self.alacritty_cfg} not exists, put it here')
            self.term = env.terminal_fallback_detect()

        self.wclass = config.get(name, {}).get("class", self.term)
        self.title = config.get(name, {}).get("title", self.wclass)
        self.font = config.get("default_font", "")
        if not self.font:
            self.font = config.get(name, {}).get("font", "Iosevka Term")
        self.font_size = config.get("default_font_size", "")
        if not self.font_size:
            self.font_size = config.get(name, {}).get("font_size", "14")
        use_one_fontstyle = config.get("use_one_fontstyle", False)
        self.font_style = config.get("default_font_style", "")
        if not self.font_style:
            self.font_style = config.get(name, {}).get("font_style", "Regular")
        if use_one_fontstyle:
            self.font_style_normal = config.get(name, {})\
                .get("font_style_normal", self.font_style)
            self.font_style_bold = config.get(name, {})\
                .get("font_style_bold", self.font_style)
            self.font_style_italic = config.get(name, {})\
                .get("font_style_italic", self.font_style)
        else:
            self.font_style_normal = config.get(name, {})\
                .get("font_style_normal", 'Regular')
            self.font_style_bold = config.get(name, {})\
                .get("font_style_bold", 'Bold')
            self.font_style_italic = config.get(name, {})\
                .get("font_style_italic", 'Italic')

        self.tmux_session_attach = \
            f"tmux -S {self.sockpath} a -t {name}"
        self.tmux_new_session = \
            f"tmux -S {self.sockpath} new-session -s {name}"
        colorscheme = config.get("colorscheme", '')
        if colorscheme:
            self.set_colorscheme = \
                f"{Misc.i3path() + 'bin/dynamic-colors'} switch {colorscheme};"
        else:
            self.set_colorscheme = ''
        self.exec = config.get(name, {}).get("exec", '')
        self.exec_tmux = config.get(name, {}).get("exec_tmux", [])
        self.with_tmux = bool(self.exec_tmux)
        if not self.with_tmux:
            exec_dtach = config.get(name, {}).get('exec_dtach', '')
            if not exec_dtach:
                self.prog = config.get(name, {}).get('exec', 'true')
            else:
                self.prog = f'dtach -A {dtach_session_dir}' \
                            f'/{name}.session {exec_dtach}'

        self.padding = config.get(name, {}).get('padding', [2, 2])
        self.opacity = config.get(name, {}).get('opacity', 0.88)
        self.statusline = config.get(name, {}).get('statusline', 1)

        self.create_term_params(config, name)

        def join_processes():
            for prc in multiprocessing.active_children():
                prc.join()

        threading.Thread(target=join_processes, args=(), daemon=True).start()

    @staticmethod
    def terminal_fallback_detect() -> str:
        """ Detect non alacritty terminal """
        for t in ['st', 'urxvt']:
            if shutil.which(t):
                return t
        print('No supported terminal installed, fail :(')
        return ''

    @staticmethod
    def create_alacritty_cfg(
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
        app_name = config.get(name, {}).get('app_name', {})
        if not app_name:
            app_name = config.get(name, {}).get('class')

        app_name = expanduser(app_name + '.yml')
        cfgname = expanduser(f'{alacritty_cfg_dir}/{app_name}')

        shutil.copyfile(
            expanduser(os.environ.get(
                "XDG_CONFIG_HOME") + "/alacritty/alacritty.yml"
            ),
            cfgname
        )

        return cfgname

    def yaml_config_create(self, custom_config: str) -> None:
        """ Create config for alacritty

            Args:
                custom_config(str): config name to create
        """
        conf = None
        with open(custom_config, "r") as cfg_file:
            try:
                conf = yaml.load(
                    cfg_file, Loader=yamlloader.ordereddict.CSafeLoader)
                if conf is not None:
                    conf["font"]["normal"]["family"] = self.font
                    conf["font"]["bold"]["family"] = self.font
                    conf["font"]["italic"]["family"] = self.font
                    conf["font"]["normal"]["style"] = self.font_style_normal
                    conf["font"]["bold"]["style"] = self.font_style_bold
                    conf["font"]["italic"]["style"] = self.font_style_italic
                    conf["font"]["size"] = self.font_size
                    conf["background_opacity"] = self.opacity
                    conf["window"]["padding"]['x'] = int(self.padding[0])
                    conf["window"]["padding"]['y'] = int(self.padding[1])
            except yaml.YAMLError as yamlerror:
                print(yamlerror)

        if conf is not None and conf:
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
        if self.term == "alacritty":
            custom_config = self.create_alacritty_cfg(
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
                "--class", self.wclass,
                "-t", self.title,
                "-e", self.default_shell, "-c"
            ]
        elif self.term == "st":
            self.term_opts = ["st"] + [
                "-c", self.wclass,
                "-f", self.font + ":size=" + str(self.font_size),
                "-e", self.default_shell, "-c",
            ]
        elif self.term == "urxvt":
            self.term_opts = ["urxvt"] + [
                "-name", self.wclass,
                "-fn", "xft:" + self.font + ":size=" + str(self.font_size),
                "-e", self.default_shell, "-c",
            ]


class executor(extension, cfg):
    """ Tmux Manager class. Easy and consistent way to create tmux sessions on
        dedicated sockets. Also it can run simply run applications without
        Tmux. The main advantage is dynamic config reloading and simplicity of
        adding or modifing of various parameters.

    Parents:
        cfg: configuration manager to autosave/autoload
                  TOML-configutation with inotify
    """
    def __init__(self, i3) -> None:
        """ Init function. """
        cfg.__init__(self, i3)
        self.envs = {}
        for app in self.cfg:
            self.envs[app] = env(app, self.cfg)

        self.bindings = {
            "run": self.run,
            "reload": self.reload_config,
        }

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.envs.clear()

    def run_app(self, args: List) -> None:
        """ Wrapper to run selected application in background. """
        subprocess.Popen(args)

    @staticmethod
    def detect_session_bind(sockpath, name) -> str:
        """ Find target session for given socket. """
        session_list = subprocess.run(
            shlex.split(f"tmux -S {sockpath} list-sessions"),
            stdout=subprocess.PIPE,
            check=False
        ).stdout
        return subprocess.run(
            shlex.split(f"awk -F ':' '/{name}/ {{print $1}}'"),
            stdout=subprocess.PIPE,
            input=(session_list),
            check=False
        ).stdout.decode()

    def attach_to_session(self) -> None:
        """ Run tmux to attach to given socket. """
        self.run_app(
            self.env.term_opts +
            [f"{self.env.set_colorscheme} {self.env.tmux_session_attach}"]
        )

    def search_classname(self) -> bytes:
        """ Search for selected window class. """
        return subprocess.run(
            shlex.split(f"xdotool search --classname {self.env.wclass}"),
            stdout=subprocess.PIPE,
            check=False
        ).stdout

    def create_new_session(self) -> None:
        """ Run tmux to create the new session on given socket. """
        exec_cmd = ''
        for pos, token in enumerate(self.env.exec_tmux):
            if pos == 0:
                exec_cmd += f'-n {token[0]} {token[1]}\\; '
            else:
                exec_cmd += f'neww -n {token[0]} {token[1]}\\; '
        if not self.env.statusline:
            exec_cmd += f'set status off\\; '
        self.run_app(
            self.env.term_opts +
            [f"{self.env.set_colorscheme} \
            {self.env.tmux_new_session} {exec_cmd} && \
                {self.env.tmux_session_attach}"]
        )

    def run(self, name: str) -> None:
        """ Entry point, run application with Tmux on dedicated socket(in most
            cases), or without tmux, if config value with_tmux=0.
            Args:
                name (str): target application name, with configuration taken
                            from TOML.
        """
        self.env = self.envs[name]
        if self.env.with_tmux:
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
