""" Terminal manager. Give simple and consistent way for user to create tmux
sessions on dedicated sockets. Also it can run simply run applications without
Tmux. The main advantage is dynamic config reloading and simplicity of adding
or modifing of various parameters, also it works is faster then dedicated
scripts, because there is no parsing / translation phase here in runtime. """

import subprocess
import os
from os.path import expanduser
import shlex
import shutil
import threading
import multiprocessing
import yaml
import yamlloader

from . extension import extension
from . cfg import cfg
from . misc import Misc


class env():
    """ Environment class. It is a helper for tmux manager to store info about currently selected application. This class rules over
    parameters and settings of application, like used terminal enumator, fonts, all path settings, etc.
    config: manager to autosave/autoload configutation with inotify """
    def __init__(self, name: str, config) -> None:
        self.name = name
        self.shell = 'dash'
        cache_dir = Misc.i3path() + '/cache'
        Misc.create_dir(cache_dir)
        tmux_socket_dir = expanduser(f'{cache_dir}/tmux_sockets')
        dtach_session_dir = expanduser(f'{cache_dir}/dtach_sessions')
        self.alacritty_cfg_dir = expanduser(f'{cache_dir}/alacritty_cfg')
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            self.alacritty_cfg = expanduser(f'{xdg_config_home}/alacritty/alacritty.yml')
        else:
            self.alacritty_cfg = expanduser('~/.config/alacritty/alacritty.yml')
        Misc.create_dir(tmux_socket_dir)
        Misc.create_dir(self.alacritty_cfg_dir)
        Misc.create_dir(dtach_session_dir)
        self.sockpath = expanduser(f'{tmux_socket_dir}/{name}.socket')
        cfg_block = config.get(name, {})
        if not cfg_block:
            return
        # Get terminal from config, use Alacritty by default
        self.term = cfg_block.get("term", "alacritty").lower()
        if os.path.exists(self.alacritty_cfg):
            if os.stat(self.alacritty_cfg).st_size == 0:
                print('Alacritty cfg {self.alacritty_cfg} is empty')
                self.term = env.terminal_fallback_detect()
        else:
            print('Alacritty cfg {self.alacritty_cfg} not exists, put it here')
            self.term = env.terminal_fallback_detect()
        self.wclass = cfg_block.get("classw", self.term)
        self.title = cfg_block.get("title", self.wclass)
        self.font = config.get("default_font", "")
        if not self.font:
            self.font = cfg_block.get("font", "Iosevka")
        self.font_size = config.get("default_font_size", "")
        if not self.font_size:
            self.font_size = cfg_block.get("font_size", "14")
        use_one_fontstyle = config.get("use_one_fontstyle", False)
        self.font_style = config.get("default_font_style", "")
        if not self.font_style:
            self.font_style = cfg_block.get("font_style", "Regular")
        if use_one_fontstyle:
            self.font_normal = cfg_block.get("font_normal", self.font_style)
            self.font_bold = cfg_block.get("font_bold", self.font_style)
            self.font_italic = cfg_block.get("font_italic", self.font_style)
        else:
            self.font_normal = cfg_block.get("font_normal", 'Regular')
            self.font_bold = cfg_block.get("font_bold", 'Bold')
            self.font_italic = cfg_block.get("font_italic", 'Italic')
        self.tmux_session_attach = f"tmux -S {self.sockpath} a -t {name}"
        self.tmux_new_session = f"tmux -S {self.sockpath} new-session -s {name}"
        self.exec = cfg_block.get("exec", '')
        self.exec_tmux = cfg_block.get("exec_tmux", [])
        self.with_tmux = bool(self.exec_tmux)
        if not self.with_tmux:
            exec_dtach = cfg_block.get('exec_dtach', '')
            if not exec_dtach:
                self.prog = cfg_block.get('exec', 'true')
            else:
                self.prog = f'dtach -A {dtach_session_dir}' \
                            f'/{name}.session {exec_dtach}'
        self.padding = cfg_block.get('padding', [2, 2])
        self.opacity = cfg_block.get('opacity', 0.88)
        self.statusline = cfg_block.get('statusline', 1)
        self.create_term_params(config, name)

        def join_processes():
            for prc in multiprocessing.active_children():
                prc.join()
        threading.Thread(target=join_processes, args=(), daemon=True).start()

    @staticmethod
    def terminal_fallback_detect() -> str:
        """ Detect non alacritty terminal """
        for t in ['st']:
            if shutil.which(t):
                return t
        print('No supported terminal installed, fail :(')
        return ''

    def create_alacritty_cfg(self, cfg_dir, config: dict, name: str) -> str:
        """ Config generator for alacritty. We need it because of alacritty
        cannot bypass most of user parameters with command line now.
        cfg_dir: alacritty config dir
        config: config dirtionary
        name(str): name of config to generate
        cfgname(str): configname """
        app_name = config.get(name, {}).get('app_name', '')
        if not app_name:
            app_name = config.get(name, {}).get('classw')
        app_name = f'{app_name}.yml'
        cfgname = expanduser(f'{cfg_dir}/{app_name}')
        shutil.copyfile(self.alacritty_cfg, cfgname)
        return cfgname

    def yaml_config_create(self, custom_config: str) -> None:
        """ Create config for alacritty
        custom_config(str): config name to create """
        conf = None
        with open(custom_config, "r", encoding="utf-8") as cfg_file:
            try:
                conf = yaml.load(
                    cfg_file, Loader=yamlloader.ordereddict.CSafeLoader)
                if conf is not None:
                    conf["font"]["normal"]["family"] = self.font
                    conf["font"]["bold"]["family"] = self.font
                    conf["font"]["italic"]["family"] = self.font
                    conf["font"]["normal"]["style"] = self.font_normal
                    conf["font"]["bold"]["style"] = self.font_bold
                    conf["font"]["italic"]["style"] = self.font_italic
                    conf["font"]["size"] = self.font_size
                    conf["window"]["opacity"] = self.opacity
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
            config(dict): config dictionary which should be adopted to
            commandline options or settings. """
        custom_config = self.create_alacritty_cfg(
            self.alacritty_cfg_dir, config, name
        )
        multiprocessing.Process(
            target=self.yaml_config_create, args=(custom_config,),
            daemon=True
        ).start()
        if self.term == 'alacritty':
            self.term_opts = [
                "alacritty", "--config-file",
                expanduser(custom_config), "--class", f'{self.wclass},{self.wclass}',
                "-t", self.title, "-e"
            ]
        elif self.term == "st":
            self.term_opts = ["st"] + [
                "-c", self.wclass,
                "-t", self.name,
                "-f", self.font + ":size=" + str(self.font_size) + f":style={self.font_normal}",
                "-e"
            ]


class executor(extension, cfg):
    """ Tmux Manager class. Easy and consistent way to create tmux sessions on
    dedicated sockets. Also it can run simply run applications without Tmux.
    The main advantage is dynamic config reloading and simplicity of adding or
    modifing of various parameters.
    cfg: configuration manager to autosave/autoload configutation with
    inotify """
    def __init__(self, i3) -> None:
        extension.__init__(self)
        cfg.__init__(self, i3)
        self.envs = {}
        for app in self.cfg:
            self.envs[app] = env(app, self.cfg)
        self.bindings = {
            "run": self.run,
            "reload": self.reload_config,
        }
        self.i3ipc = i3

    def __exit__(self) -> None:
        self.envs.clear()

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
        cmd = f"exec \"{' '.join(self.env.term_opts)}" \
            f" {self.env.shell} -i -c" \
            f" \'{self.env.tmux_session_attach}\'\""
        self.i3ipc.command(cmd)

    def create_new_session(self) -> None:
        """ Run tmux to create the new session on given socket. """
        exec_cmd = ''
        for pos, token in enumerate(self.env.exec_tmux):
            if 0 == pos:
                exec_cmd += f'-n {token[0]} {token[1]}\\; '
            else:
                exec_cmd += f'neww -n {token[0]} {token[1]}\\; '
        if not self.env.statusline:
            exec_cmd += 'set status off\\; '
        cmd = f"exec \"{' '.join(self.env.term_opts)}" + \
            f" {self.env.shell} -i -c" \
            f" \'{self.env.tmux_new_session}" + \
            f" {exec_cmd} && {self.env.tmux_session_attach}\'\""
        self.i3ipc.command(cmd)

    def run(self, name: str) -> None:
        """ Entry point, run application with Tmux on dedicated socket(in most
        cases), or without tmux, if config value with_tmux=0
        name (str): target application name, taken from config file """
        self.env = self.envs[name]
        if self.env.with_tmux:
            if self.env.name in self.detect_session_bind(
                    self.env.sockpath, self.env.name):
                if not self.i3ipc.get_tree().find_classed(self.env.wclass):
                    self.attach_to_session()
            else:
                self.create_new_session()
        else:
            cmd = f"exec \"{' '.join(self.env.term_opts)} {self.env.prog}\""
            self.i3ipc.command(cmd)
