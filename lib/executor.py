''' Terminal manager. Give simple and consistent way for user to create tmux
sessions on dedicated sockets. Also it can run simply run applications without
Tmux. The main advantage is dynamic config reloading and simplicity of adding
or modifing of various parameters, also it works is faster then dedicated
scripts, because there is no parsing / translation phase here in runtime. '''

import subprocess
import os
from os.path import expanduser
import shlex
import shutil
import threading
import multiprocessing
import yaml
import yamlloader
import logging

from . extension import extension
from . cfg import cfg
from . misc import Misc


class env():
    ''' Environment class. It is a helper for tmux manager to store info about currently selected application. This class rules over
    parameters and settings of application, like used terminal enumator, fonts, all path settings, etc.
    config: manager to autosave/autoload configutation with inotify '''

    tmux_socket_dir = expanduser(f'{Misc.cache_path()}/tmux_sockets')
    dtach_session_dir = expanduser(f'{Misc.cache_path()}/dtach_sessions')
    alacritty_cfg_dir = expanduser(f'{Misc.cache_path()}/alacritty_cfg')
    alacritty_cfg = expanduser(f'{Misc.xdg_config_home()}/alacritty/alacritty.yml')

    def __init__(self, name: str, config) -> None:
        self.name, self.config = name, config
        if not self.cfg_block():
            logging.error(f'Cannot create config for {name}, with config {config}')
            return

        Misc.create_dir(Misc.cache_path())
        for dir in env.tmux_socket_dir, env.alacritty_cfg_dir, env.dtach_session_dir:
            Misc.create_dir(dir)

        # Get terminal from config, use Alacritty by default
        self.term = self.cfg_block().get("term", "alacritty").lower()
        if os.path.exists(env.alacritty_cfg):
            if os.stat(env.alacritty_cfg).st_size == 0:
                logging.error(f'Alacritty cfg {env.alacritty_cfg} is empty')
                self.term = env.terminal_fallback_detect()
        else:
            logging.error(f'Alacritty cfg {env.alacritty_cfg} not exists, put it here')
            self.term = env.terminal_fallback_detect()

        self.sockpath = expanduser(f'{env.tmux_socket_dir}/{name}.socket')
        self.tmux_session_attach = f"tmux -S {self.sockpath} a -t {name}"
        self.tmux_new_session = f"tmux -S {self.sockpath} new-session -s {name}"

        self.exec_tmux = self.cfg_block().get("exec_tmux", [])
        if not self.exec_tmux:
            exec_dtach = self.cfg_block().get('exec_dtach', '')
            if not exec_dtach:
                self.exec = self.cfg_block().get('exec', 'true')
            else:
                self.exec = f'dtach -A {env.dtach_session_dir}' \
                            f'/{name}.session {exec_dtach}'

        self.create_term_params(name)

        def join_processes():
            for prc in multiprocessing.active_children():
                prc.join()
        threading.Thread(target=join_processes, args=(), daemon=True).start()

    def cfg_block(self) -> dict:
        return self.config.get(self.name, {})

    def shell(self) -> str:
        return self.cfg_block().get('shell', 'dash')

    def font(self) -> str:
        ret = self.config.get('default_font', '')
        if not ret:
            ret = self.cfg_block().get('font', 'Iosevka')
        return ret

    def font_size(self) -> str:
        ret = self.config.get('default_font_size', '')
        if not ret:
            ret = self.cfg_block().get('font_size', '14')
        return ret

    def style(self) -> dict:
        use_one_fontstyle = self.config.get('use_one_fontstyle', False)
        style = self.config.get('default_style', '')
        if not style:
            style = self.cfg_block().get('style', 'Regular')
        if use_one_fontstyle:
            return {
                'normal': self.cfg_block().get('font_normal', style),
                'bold' : self.cfg_block().get('font_bold', style),
                'italic': self.cfg_block().get('font_italic', style)
            }
        else:
            return {
                'normal': self.cfg_block().get('font_normal', 'Regular'),
                'bold' : self.cfg_block().get('font_bold', 'Bold'),
                'italic': self.cfg_block().get('font_italic', 'Italic')
            }

    @staticmethod
    def terminal_fallback_detect() -> str:
        ''' Detect non alacritty terminal '''
        for t in ['st', 'kitty', 'zutty']:
            if shutil.which(t):
                return t
        logging.error('No supported terminal installed, fail :(')
        return ''

    def yaml_config_create(self, custom_config: str) -> None:
        ''' Create config for alacritty
        custom_config(str): config name to create '''
        conf = None
        with open(custom_config, 'r', encoding='utf-8') as cfg_file:
            try:
                conf = yaml.load(
                    cfg_file, Loader=yamlloader.ordereddict.CSafeLoader)
                if conf is not None:
                    if 'font' in conf:
                        font = conf['font']
                        font['normal']['family'] = self.font()
                        font['bold']['family'] = self.font()
                        font['italic']['family'] = self.font()
                        font['normal']['style'] = self.style()['normal']
                        font['bold']['style'] = self.style()['bold']
                        font['italic']['style'] = self.style()['italic']
                        font['size'] = self.font_size()
                    if 'window' in conf:
                        window = conf['window']
                        padding = self.cfg_block().get('padding', [2, 2])
                        opacity = self.cfg_block().get('opacity', 0.88)
                        window['opacity'] = opacity
                        window['padding']['x'] = int(padding[0])
                        window['padding']['y'] = int(padding[1])
            except yaml.YAMLError as yamlerror:
                logging.error(yamlerror)

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
                    logging.error(yamlerror)

    def create_alacritty_cfg(self, name: str) -> str:
        ''' Config generator for alacritty. We need it because of alacritty
        cannot bypass most of user parameters with command line now.
        cfg_dir: alacritty config dir
        config: config dirtionary
        name(str): name of config to generate
        cfgname(str): configname '''
        app_name = self.config.get(name, {}).get('app_name', '')
        if not app_name:
            app_name = self.config.get(name, {}).get('classw')
        app_name = f'{app_name}.yml'
        cfgname = expanduser(f'{env.alacritty_cfg_dir}/{app_name}')
        shutil.copyfile(env.alacritty_cfg, cfgname)
        return cfgname

    def alacritty_term(self, name):
        self.title = self.cfg_block().get("title", self.wclass)
        custom_config = self.create_alacritty_cfg(name)
        multiprocessing.Process(
            target=self.yaml_config_create, args=(custom_config,),
            daemon=True
        ).start()

        return [
            f"{self.term}",
            f"--config-file {expanduser(custom_config)}",
            f"--class {self.wclass},{self.wclass}",
            f"-t {self.title} -e"]

    def st_term(self):
        return [
            f"{self.term}",
            f"-c {self.wclass}",
            f"-t {self.name}",
            f"-f {self.font} :size={str(self.font_size())}:style={self.style()['normal']}",
            "-e"]

    def kitty_term(self):
        padding = self.cfg_block().get('padding', [0, 0])[0]
        opacity = self.cfg_block().get('opacity', 0.88)
        return [
            f"{self.term}",
            f"--class={self.wclass}",
            f"--title={self.name}",
            f"-o window_padding_width={padding}",
            f"-o background_opacity={opacity}",
            f"-o font_family='{self.font()} {self.style()['normal']}'",
            f"-o font_size={str(self.font_size())}"]

    def zutty_term(self):
        return [
            f"{self.term}",
            f"-name {self.wclass}",
            f"-font {self.font}",
            f"-fontsize {str(self.font_size())}"]

    def create_term_params(self, name: str) -> None:
        ''' This function fill self.opts for settings.abs
            config(dict): config dictionary which should be adopted to
            commandline options or settings. '''
        self.wclass = self.cfg_block().get("classw", self.term)

        if self.term == 'alacritty':
            self.opts = self.alacritty_term(name)
        elif self.term == 'st':
            self.opts =self.st_term()
        elif self.term == 'kitty':
            self.opts = self.kitty_term()
        elif self.term == 'zutty':
            self.opts = self.zutty_term()

class executor(extension, cfg):
    ''' Tmux Manager class. Easy and consistent way to create tmux sessions on
    dedicated sockets. Also it can run simply run applications without Tmux.
    The main advantage is dynamic config reloading and simplicity of adding or
    modifing of various parameters.
    cfg: configuration manager to autosave/autoload configutation with
    inotify '''
    def __init__(self, i3) -> None:
        extension.__init__(self)
        cfg.__init__(self, i3)
        self.envs = {}
        for app in self.cfg:
            self.envs[app] = env(app, self.cfg)
        self.i3ipc = i3

    def __exit__(self) -> None:
        self.envs.clear()

    @staticmethod
    def detect_session_bind(sockpath, name) -> str:
        ''' Find target session for given socket. '''
        session_list = subprocess.run(
            shlex.split(f'tmux -S {sockpath} list-sessions'),
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
        ''' Run tmux to attach to given socket. '''
        cmd = f"exec \"{' '.join(self.env.opts)}" \
            f" {self.env.shell()} -i -c" \
            f" \'{self.env.tmux_session_attach}\'\""
        self.i3ipc.command(cmd)

    def create_new_session(self) -> None:
        ''' Run tmux to create the new session on given socket. '''
        exec_cmd = ''
        for pos, token in enumerate(self.env.exec_tmux):
            if 0 == pos:
                exec_cmd += f'-n {token[0]} {token[1]}\\; '
            else:
                exec_cmd += f'neww -n {token[0]} {token[1]}\\; '
        if not self.env.cfg_block().get('statusline', 1):
            exec_cmd += 'set status off\\; '
        cmd = f"exec \"{' '.join(self.env.opts)}" + \
            f" {self.env.shell()} -i -c" \
            f" \'{self.env.tmux_new_session}" + \
            f" {exec_cmd} && {self.env.tmux_session_attach}\'\""
        self.i3ipc.command(cmd)

    def run(self, name: str) -> None:
        ''' Entry point, run application with Tmux on dedicated socket(in most
        cases), or without tmux, exec_tmux is empty.
        name (str): target application name, taken from config file '''
        self.env = self.envs[name]
        if self.env.exec_tmux:
            if self.env.name in self.detect_session_bind(
                    self.env.sockpath, self.env.name):
                if not self.i3ipc.get_tree().find_classed(self.env.wclass):
                    self.attach_to_session()
            else:
                self.create_new_session()
        else:
            cmd = f"exec \"{' '.join(self.env.opts)} {self.env.exec}\""
            self.i3ipc.command(cmd)
